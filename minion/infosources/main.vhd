library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library machxo2;
use machxo2.all;

entity odmrCounter is
	port(
		clkin   : in std_logic;
		clken   : out std_logic;
		led     : buffer std_logic_vector(7 downto 0);
		RS232_Rx: in std_logic;
		RS232_Tx: out std_logic;
		inputs: in std_logic_vector(4 downto 0);
		outputs: buffer std_logic_vector(5 downto 0));
	constant controlClockrate		: integer	:= 40000000;
	constant countClockrate			: integer	:= 80000000;
	constant baudrate				: integer	:= 4000000;
	constant RS232_Tx_buffer_size	: integer	:= 16;
	constant numCounters			: integer	:= 2;
	constant defaultTriggerInput	: integer 	:= 4;
end odmrCounter;

architecture behaviour of odmrCounter is
	type communication_instructions is (init, wait_rs232_read_instruction,
--	wait_rs232_read_counter_id,
		wait_rs232_read_timeout, wait_rs232_read_predelay, process_predelay,
		wait_rs232_read_address, wait_rs232_read_number_of_counts,
--		wait_rs232_read_number_of_counts_8bit_only,
		wait_countImmediately, wait_rs232_transfer,
		wait_rs232_read_number_of_triggeredCountingBins,
		wait_rs232_read_outputs, wait_rs232_read_trigger_mask,
		wait_rs232_read_triggeredCountingBinRepetitions,
		wait_rs232_read_trigger_inverts, wait_rs232_read_flags,
		dumpCounterMemory, resetCounterMemory_init, resetCounterMemory
);
	type counter_instructions is (
		idle,								--000
		immediateCounting_start,			--001
		immediateCounting_waitForTimeout,	--010
		triggeredCounting_waitForTrigger,	--011
		triggeredCounting_store,			--100
		triggeredCounting_predelay,			--101
		triggeredCounting_prestore,			--110
		triggeredCounting_waitForTimeout 	--111
);
	type asynchronouos_control_commands is (none, gotoIdle, copyAddress,
		reset, countImmediately, countTriggered, trigger);
	type asynchronous_results is (none, ok, completed, error);
	subtype int16 is signed(15 downto 0);
	subtype uint16 is unsigned(15 downto 0);
	subtype int32 is signed(31 downto 0);
	subtype uint32 is unsigned(31 downto 0);
	type counter_array_type is array(numCounters-1 downto 0) of uint32;
	subtype triggeredCounting_address_type is unsigned(11 downto 0);
	subtype triggeredCounting_data_type is unsigned(17 downto 0);
	type triggeredCounting_address_array_type is array(numCounters-1 downto 0)
		of triggeredCounting_address_type;
	type triggeredCounting_data_array_type is array(numCounters-1 downto 0)
		of triggeredCounting_data_type;
	
	constant triggeredCounting_address_zero : triggeredCounting_address_type
		:= to_unsigned(0,triggeredCounting_address_type'length);
	
	component odmrControlClock
		port(CLKI: in std_logic; CLKOP: out std_logic;
			CLKOS: out std_logic; CLKOS2: out std_logic; CLKOS3: out std_logic);
	end component;
	component odmrCounterClock
		port(CLKI: in std_logic; CLKOP: out std_logic;
			CLKOS: out std_logic; CLKOS2: out std_logic; CLKOS3: out std_logic);
	end component;
	
	component RS232
		generic ( clockrate: integer; baudrate: integer ); 
		port(
			RXD     : in  std_logic;
			RX_Data : out std_logic_vector (7 downto 0);
            RX_Busy : out std_logic;
            TXD     : out std_logic;
            TX_Data : in  std_logic_vector (7 downto 0);
            TX_Start: in  std_logic;
			TX_Busy : out std_logic;
			CLK     : in  std_logic);
	end component;
--	component CounterRam
--	port (Clock: in  std_logic; ClockEn: in  std_logic; 
--		Reset: in  std_logic; WE: in  std_logic; 
--		Address: in  std_logic_vector(11 downto 0); 
--		Data: in  std_logic_vector(17 downto 0); 
--		Q: out  std_logic_vector(17 downto 0));
--	end component;
	component counterRam
	port (	DataInA: in  std_logic_vector(17 downto 0); 
		DataInB: in  std_logic_vector(17 downto 0); 
		AddressA: in  std_logic_vector(11 downto 0); 
		AddressB: in  std_logic_vector(11 downto 0); 
		ClockA: in  std_logic; 
		ClockB: in  std_logic; 
		ClockEnA: in  std_logic; 
		ClockEnB: in  std_logic; 
		WrA: in  std_logic; 
		WrB: in  std_logic; 
		ResetA: in  std_logic; 
		ResetB: in  std_logic; 
		QA: out  std_logic_vector(17 downto 0); 
		QB: out  std_logic_vector(17 downto 0));
	end component;
	component inputCounter
		port(input: in std_logic; clk: in std_logic; gate: in std_logic; reset: in std_logic;
			count: buffer uint32);
	end component;
	
	signal controlClk      	: std_logic_vector(0 to 3);
	signal countClk      	: std_logic_vector(0 to 3);
	signal counter_clock	: uint32 := to_unsigned(0,32);
	signal counters			: counter_array_type;
	signal counters_reset	: std_logic_vector(numCounters-1 downto 0)
					:= std_logic_vector(to_unsigned(0,numCounters));
	signal counting_stopped	: std_logic := '1';
	signal timeout		: uint32 := to_unsigned(0,32);
	signal RS232_Rx_data	: std_logic_vector(7 downto 0);
	signal RS232_Tx_data	: std_logic_vector(7 downto 0);
	signal RS232_Rx_busy	: std_logic;
	signal RS232_Tx_busy	: std_logic;
	signal RS232_Tx_start	: std_logic := '0';
	signal number_of_counts	: uint32 := to_unsigned(0,32);

	signal triggeredCountingWorkAddress		: triggeredCounting_address_type;
	signal triggeredCountingWorkDataIn		: triggeredCounting_data_array_type;
	signal triggeredCountingWorkDataOut		: triggeredCounting_data_array_type;
	signal triggeredCountingWorkWriteEnable	: std_logic_vector(numCounters-1 downto 0) 
								:= std_logic_vector(to_unsigned(0,numCounters));
	signal triggeredCountingDumpAddress		: triggeredCounting_address_type;
--	signal triggeredCountingDumpDataIn		: triggeredCounting_data_array_type;
	signal triggeredCountingDumpDataOut		: triggeredCounting_data_array_type;
	signal triggeredCountingDumpWriteEnable	: std_logic_vector(numCounters-1 downto 0) 
								:= std_logic_vector(to_unsigned(0,numCounters));
	signal triggeredCountingTrigger			: std_logic;
	signal triggeredCountingTriggerBuffer	: std_logic := '0';
	signal triggeredCountingTriggerAck		: std_logic := '0';
	signal triggeredCountingTriggerMask		: std_logic_vector(inputs'length-1 downto 0)
								:= std_logic_vector(to_unsigned(2**defaultTriggerInput,inputs'length));
	signal triggeredCountingTriggerInvert	: std_logic_vector(inputs'length-1 downto 0)
								:= std_logic_vector(to_unsigned(0,inputs'length));
	signal triggeredCountingTriggerPolarity	: std_logic := '0';
	
	signal triggeredCountingBins			: triggeredCounting_address_type
								:= triggeredCounting_address_zero;
	signal triggeredCountingBinRepetitions	: uint16 := to_unsigned(0,16);
	signal triggeredCountingBinRepetitionCounter
											: uint16 := to_unsigned(0,16);
	signal splitTriggeredCountingBins		: boolean := false;

	signal predelay							: uint32 := to_unsigned(0,32);
	signal enablePredelay					: boolean := false;
	
	signal communicationInstruction					: communication_instructions := init;
	signal instructionAfterRS232Transfer	: communication_instructions
								:= wait_rs232_read_instruction;
	signal counterInstruction				: counter_instructions := idle;
	signal asyncControlCommand,asyncControlCommandBuffer
											: asynchronouos_control_commands := none;
	signal asyncControlCommandSignal, asyncControlCommandSignalBuffer, 
		asyncControlCommandSignalAck		: std_logic := '0';
--	signal asyncResult,asyncResultBuffer	: asynchronous_results := none;
--	signal asyncResultSignal,asyncResultSignalBuffer,asyncResultSignalAck
	signal asyncCompletion, asyncCompletionBuffer, asyncCompletionAck
											: std_logic := '0';
--	signal bytes_to_read_s: unsigned(7 downto 0);
--	signal bytes_to_write_s: unsigned(7 downto 0);

--	signal debugState : unsigned(1 downto 0) := "00";

	function maskedOr(sig: std_logic_vector; mask: std_logic_vector) return std_logic is
		variable t: std_logic := 'Z';
	begin
		for i in sig'range loop
			t := t or (sig(i) and mask(i));
		end loop;
		return t;
	end function;
	
	function Boolean_to_Std_Logic(x : boolean) return std_logic is
	begin
		if x then
			return '1';
		else
			return '0';
		end if;
	end function;

	function Std_Logic_to_Boolean(x : std_logic) return boolean is
	begin
		return x = '1' or x = 'H';
	end function;

begin
	odmrControlClockInst0: odmrControlClock port map(CLKI => clkin, CLKOP => controlClk(0),
		CLKOS => controlClk(1), CLKOS2 => controlClk(2), CLKOS3 => controlClk(3));
	odmrCounterClockInst0: odmrCounterClock port map(CLKI => clkin, CLKOP => countClk(0),
		CLKOS => countClk(1), CLKOS2 => countClk(2), CLKOS3 => countClk(3));
	RS232Inst0: RS232 generic map(clockrate => controlClockrate, baudrate => baudrate)
		port map(TXD => RS232_Tx, TX_Data => RS232_Tx_data, TX_Busy =>RS232_Tx_busy,
			TX_Start => RS232_Tx_start, RXD => RS232_Rx, RX_Data => RS232_Rx_data,
			RX_Busy => RS232_Rx_busy, CLK => controlClk(1));
	counterInsts: for i in counters'right to counters'left generate
	begin
		counterInst: inputCounter port map(input => inputs(i),
				gate => not counting_stopped, clk => countClk(1), reset => counters_reset(i),
				count => counters(i));
	end generate counterInsts;
	counterRamInsts: for i in counters'right to counters'left generate
	begin 
		counterRamInst: counterRam port map (
			ClockA=>countClk(2), ClockEnA=>'1', ResetA=>'0',
			WrA=>triggeredCountingWorkWriteEnable(i),
			AddressA=>std_logic_vector(triggeredCountingWorkAddress),
			DataInA=>std_logic_vector(triggeredCountingWorkDataIn(i)),
			unsigned(QA)=>triggeredCountingWorkDataOut(i),
			ClockB=>controlClk(2), ClockEnB=>'1', ResetB=>'0',
			WrB=>triggeredCountingDumpWriteEnable(i),
			AddressB=>std_logic_vector(triggeredCountingDumpAddress),
--			DataInB=>std_logic_vector(triggeredCountingDumpDataIn(i)),
			DataInB=>std_logic_vector(to_unsigned(0,triggeredCounting_data_type'length)),
			unsigned(QB)=>triggeredCountingDumpDataOut(i));
	end generate counterRamInsts;

	clken <= '1';
	led <= not std_logic_vector(number_of_counts(7 downto 0));
--	outputs(4) <= '1' when asyncResult = completed else '0';
--	outputs(5) <= '1' when asyncResult = error else '0';
--	outputs(3) <= triggeredCountingTriggerAck;

	triggeredCountingTrigger <= triggeredCountingTriggerPolarity 
			when unsigned((inputs xor triggeredCountingTriggerInvert) and triggeredCountingTriggerMask)
					= to_unsigned(0,inputs'length)
			else not triggeredCountingTriggerPolarity;
			
--	asyncControlCommandSignal <= '1' when asyncControlCommand /= none else '0';
--	asyncResultSignal <= '1' when asyncResult /= none else '0';
	
--	process(asyncResultSignal,asyncResultSignalAck)
--	begin
--		if(asyncResultSignalAck = '1') then
--			asyncResultSignalBuffer <= '0';
--		else
--			if(RISING_EDGE(asyncResultSignal)) then
--				asyncResultSignalBuffer <= '1';
--			end if;
--			asyncResultBuffer <= asyncResult;
--		end if;
--	end process;

	process(asyncCompletion,asyncCompletionAck)
	begin
		if(asyncCompletionAck = '1') then
			asyncCompletionBuffer <= '0';
		elsif(RISING_EDGE(asyncCompletion)) then
			asyncCompletionBuffer <= '1';
		end if;
	end process;

	process(controlClk(0))
--		variable communicationInstruction: communication_instructions := wait_rs232_read_instruction;
--		variable instructionAfterRS232Transfer: communication_instructions := wait_rs232_read_instruction;
		variable bytes_to_read			: integer range 0 to 255 := 0;
		variable bytes_to_write			: integer range 0 to 255 := 0;
		variable RS232_Tx_buffer		: std_logic_vector((8*RS232_Tx_buffer_size-1) downto 0);
		variable RS232_Rx_busy_last		: std_logic := '0';
		variable RS232_Tx_busy_last		: std_logic := '0';
--		variable asyncResultBufferValid	: boolean := false;
		variable asyncCompletionDetected: boolean := false;
	begin
		if(RISING_EDGE(controlClk(0))) then
--			asyncControlCommand <= none;
			asyncControlCommandSignal <= '0';
--			if(asyncResultSignalAck = '1') then
--				asyncResultSignalAck <= '0';
--				asyncResultBufferValid := true;
--			else
--				asyncResultSignalAck <= asyncResultSignalBuffer;
--				asyncResultBufferValid := false;
--			end if;
--			if(asyncResultBufferValid) then
--				case asyncResultBuffer is
--				when completed =>
--					number_of_counts <= number_of_counts + 1;
--				when error =>
--					number_of_counts <= X"FF";
--				when others =>
--				end case;
--			end if;
			if(asyncCompletionAck = '1') then
				asyncCompletionAck <= '0';
				asyncCompletionDetected := true;
				number_of_counts <= number_of_counts + 1;
			else
				asyncCompletionAck <= asyncCompletionBuffer;
				asyncCompletionDetected := false;
			end if;
			case communicationInstruction is
			when init =>
				asyncControlCommand <= gotoIdle;
				asyncControlCommandSignal <= '1';
				communicationInstruction <= wait_rs232_read_instruction;
				predelay <= to_unsigned(0,32);
				enablePredelay <= false;
				splitTriggeredCountingBins <= false;
			when wait_rs232_read_instruction =>
				instructionAfterRS232Transfer <= wait_rs232_read_instruction;
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					case character'val(to_integer(unsigned(RS232_Rx_data))) is
					when 'C' =>
						if(counterInstruction = idle) then 
							asyncControlCommand <= countImmediately;
							asyncControlCommandSignal <= '1';
							communicationInstruction <= wait_countImmediately;
						end if;
					when 'T' =>
						bytes_to_read := 4;
						communicationInstruction <= wait_rs232_read_timeout;
					when 't' =>
						RS232_Tx_buffer(8*(bytes_to_write+4)-1 downto 8*bytes_to_write)
							:= std_logic_vector(timeout);
						bytes_to_write := bytes_to_write + 4;
						communicationInstruction <= wait_rs232_transfer;
					when 'P' =>
						bytes_to_read := 4;
						communicationInstruction <= wait_rs232_read_predelay;
					when 'p' =>
						if(enablePredelay) then 
							RS232_Tx_buffer(8*(bytes_to_write+4)-1 downto 8*bytes_to_write)
								:= std_logic_vector(predelay + 1);
						else
							RS232_Tx_buffer(8*(bytes_to_write+4)-1 downto 8*bytes_to_write)
								:= std_logic_vector(to_unsigned(0,32));
						end if;
						bytes_to_write := bytes_to_write + 4;
						communicationInstruction <= wait_rs232_transfer;
					when 'A' =>
						bytes_to_read := 2;
						communicationInstruction <= wait_rs232_read_address;
					when 'a' =>
						RS232_Tx_buffer(8*(bytes_to_write+2)-1 downto 8*bytes_to_write)
							:= std_logic_vector(to_unsigned(0,16-triggeredCountingWorkAddress'length))
								& std_logic_vector(triggeredCountingWorkAddress);
						bytes_to_write := bytes_to_write + 2;
						communicationInstruction <= wait_rs232_transfer;
					when 'L' =>
						bytes_to_read := 4;
						communicationInstruction <= wait_rs232_read_number_of_counts;
					when 'l' =>
						RS232_Tx_buffer(8*(bytes_to_write+4)-1 downto 8*bytes_to_write)
							:= std_logic_vector(number_of_counts);
						bytes_to_write := bytes_to_write + 4;
						communicationInstruction <= wait_rs232_transfer;
--					when 'N' =>
--						bytes_to_read := 1;
--						communicationInstruction <= wait_rs232_read_number_of_counts_8bit_only;
--					when 'n' =>
--						RS232_Tx_buffer(8*(bytes_to_write+1)-1 downto 8*bytes_to_write)
--							:= std_logic_vector(number_of_counts(7 downto 0));
--						bytes_to_write := bytes_to_write + 1;
--						communicationInstruction <= wait_rs232_transfer;
--					when 'I' =>
--						 number_of_counts <= number_of_counts + 1;
--					when 'i' =>
--						 number_of_counts <= number_of_counts - 1;
					when 'B' =>
						bytes_to_read := 2;
						communicationInstruction <= wait_rs232_read_number_of_triggeredCountingBins;
					when 'b' =>
						RS232_Tx_buffer(8*(bytes_to_write+2)-1 downto 8*bytes_to_write)
							:= std_logic_vector(to_unsigned(0,16-triggeredCountingBins'length))
								& std_logic_vector(triggeredCountingBins);
						bytes_to_write := bytes_to_write + 2;
						communicationInstruction <= wait_rs232_transfer;
					when 'O' =>
						bytes_to_read := 1;
						communicationInstruction <= wait_rs232_read_outputs;
					when 'o' =>
						RS232_Tx_buffer(8*(bytes_to_write+1)-1 downto 8*bytes_to_write)
							:= std_logic_vector(to_unsigned(0,8-outputs'length)) & outputs;
						bytes_to_write := bytes_to_write + 1;
						communicationInstruction <= wait_rs232_transfer;
					when '0' =>
						asyncControlCommand <= reset;
						asyncControlCommandSignal <= '1';
						communicationInstruction <= resetCounterMemory_init;
					when 'r' =>
						if(counterInstruction /= idle) then
							asyncControlCommand <= gotoIdle;
							asyncControlCommandSignal <= '1';
						end if;
					when 'R' =>
						if(counterInstruction = idle) then
							asyncControlCommand <= countTriggered;
							asyncControlCommandSignal <= '1';
						end if;
					when 'd' =>
						triggeredCountingDumpAddress <= triggeredCounting_address_zero;
						communicationInstruction <= dumpCounterMemory;
					when 'M' =>
						bytes_to_read := 1;
						communicationInstruction <= wait_rs232_read_trigger_mask;
					when 'm' =>
						RS232_Tx_buffer(8*(bytes_to_write+1)-1 downto 8*bytes_to_write)
							:= std_logic_vector(to_unsigned(0,8-triggeredCountingTriggerMask'length)) & 
								triggeredCountingTriggerMask;
						bytes_to_write := bytes_to_write + 1;
						communicationInstruction <= wait_rs232_transfer;
					when 'Q' =>
						bytes_to_read := 1;
						communicationInstruction <= wait_rs232_read_trigger_inverts;
					when 'q' =>
						RS232_Tx_buffer(8*(bytes_to_write+1)-1 downto 8*bytes_to_write)
							:= std_logic_vector(triggeredCountingTriggerPolarity
								& to_unsigned(0,7-triggeredCountingTriggerInvert'length))
								& triggeredCountingTriggerInvert;
						bytes_to_write := bytes_to_write + 1;
						communicationInstruction <= wait_rs232_transfer;
					when '!' =>
						asyncControlCommand <= trigger;
						asyncControlCommandSignal <= '1';
					when 'j' =>
						RS232_Tx_buffer(8*(bytes_to_write+2)-1 downto 8*bytes_to_write)
							:= std_logic_vector(triggeredCountingBinRepetitionCounter);
						bytes_to_write := bytes_to_write + 2;
						communicationInstruction <= wait_rs232_transfer;						
					when 'K' =>
						bytes_to_read := 2;
						communicationInstruction <= wait_rs232_read_triggeredCountingBinRepetitions;
					when 'k' =>
						RS232_Tx_buffer(8*(bytes_to_write+2)-1 downto 8*bytes_to_write)
							:= std_logic_vector(triggeredCountingBinRepetitions);
						bytes_to_write := bytes_to_write + 2;
						communicationInstruction <= wait_rs232_transfer;
					when 'F' =>
						bytes_to_read := 1;
						communicationInstruction <= wait_rs232_read_flags;
					when 'f' =>
						RS232_Tx_buffer(8*(bytes_to_write+1)-1 downto 8*bytes_to_write)
							:= std_logic_vector(to_unsigned(0,7))
								& Boolean_to_Std_Logic(splitTriggeredCountingBins);
						bytes_to_write := bytes_to_write + 1;
						communicationInstruction <= wait_rs232_transfer;
					when others =>
					end case;
				end if;		
			when wait_rs232_read_number_of_counts =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						number_of_counts <= unsigned(RS232_Rx_data)
							& number_of_counts(number_of_counts'left downto 8);
						bytes_to_read := bytes_to_read - 1;
					end if;
					if(bytes_to_read = 0) then
						communicationInstruction <= wait_rs232_read_instruction;
					end if;
				end if;
--			when wait_rs232_read_number_of_counts_8bit_only =>
--				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
--					if(bytes_to_read > 0) then
--						number_of_counts(7 downto 0) <= unsigned(RS232_Rx_data);
--						bytes_to_read := 0;
--					end if;
--					communicationInstruction <= wait_rs232_read_instruction;
--				end if;
			when wait_rs232_read_timeout =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						timeout <= unsigned(RS232_Rx_data) & timeout(timeout'left downto 8);
						bytes_to_read := bytes_to_read - 1;
					end if;
					if(bytes_to_read = 0) then
						communicationInstruction <= wait_rs232_read_instruction;
					end if;
				end if;								
			when wait_rs232_read_predelay =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						predelay <= unsigned(RS232_Rx_data) & predelay(predelay'left downto 8);
						bytes_to_read := bytes_to_read - 1;
					end if;
					if(bytes_to_read = 0) then
						communicationInstruction <= process_predelay;
					end if;
				end if;								
			when process_predelay =>
				if(predelay > 0) then
					enablePredelay <= true;
					predelay <= predelay - 1;
				else
					enablePredelay <= false;
				end if;
				communicationInstruction <= wait_rs232_read_instruction;
			when wait_rs232_read_address =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					case bytes_to_read is
					when 2 =>
						triggeredCountingDumpAddress(7 downto 0) <= unsigned(RS232_Rx_data);
						bytes_to_read := 1;
					when 1 =>
						triggeredCountingDumpAddress(triggeredCountingDumpAddress'left downto 8)
							<= unsigned(RS232_Rx_data(triggeredCountingDumpAddress'left-8 downto 0));
						bytes_to_read := 0;
						asyncControlCommand <= copyAddress;
						asyncControlCommandSignal <= '1';
					when others =>
						bytes_to_read := 0;
					end case;
					if(bytes_to_read = 0) then
						communicationInstruction <= wait_rs232_read_instruction;
					end if;
				end if;
			when wait_rs232_read_number_of_triggeredCountingBins =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					case bytes_to_read is
					when 2 =>
						triggeredCountingBins(7 downto 0) <= unsigned(RS232_Rx_data);
						bytes_to_read := 1;
					when 1 =>
						triggeredCountingBins(triggeredCountingBins'left downto 8)
							<= unsigned(RS232_Rx_data(triggeredCountingBins'left-8 downto 0));
						bytes_to_read := 0;
					when others =>
						bytes_to_read := 0;
					end case;
					if(bytes_to_read = 0) then
						communicationInstruction <= wait_rs232_read_instruction;
					end if;
				end if;
			when wait_rs232_read_outputs =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						outputs(3 downto 0) <= RS232_Rx_data(3 downto 0);
						bytes_to_read := 0;
					end if;
					communicationInstruction <= wait_rs232_read_instruction;
				end if;
			when wait_rs232_read_trigger_mask =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						triggeredCountingTriggerMask <=
							RS232_Rx_data(triggeredCountingTriggerMask'length-1 downto 0);
						bytes_to_read := 0;
					end if;
					communicationInstruction <= wait_rs232_read_instruction;
				end if;
			when wait_rs232_read_trigger_inverts =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						triggeredCountingTriggerInvert <=
							RS232_Rx_data(triggeredCountingTriggerInvert'length-1 downto 0);
						triggeredCountingTriggerPolarity <= RS232_Rx_data(7);
						bytes_to_read := 0;
					end if;
					communicationInstruction <= wait_rs232_read_instruction;
				end if;
			when wait_rs232_read_triggeredCountingBinRepetitions =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						triggeredCountingBinRepetitions <= unsigned(RS232_Rx_data) 
							& triggeredCountingBinRepetitions(
								triggeredCountingBinRepetitions'left downto 8);
						bytes_to_read := bytes_to_read - 1;
					end if;
					if(bytes_to_read = 0) then
						communicationInstruction <= wait_rs232_read_instruction;
					end if;
				end if;						
			when wait_rs232_read_flags =>
				if(RS232_Rx_busy_last = '1' and RS232_Rx_busy = '0') then
					if(bytes_to_read > 0) then
						splitTriggeredCountingBins <= Std_Logic_to_Boolean(RS232_Rx_data(0));
						bytes_to_read := 0;
						communicationInstruction <= wait_rs232_read_instruction;
					end if;
				end if;						
			when wait_rs232_transfer =>
				if(RS232_Tx_busy = '0') then
					if(bytes_to_write > 0) then
						RS232_Tx_data <= RS232_Tx_buffer(7 downto 0);
						RS232_Tx_buffer := X"00"
							& RS232_Tx_buffer(RS232_Tx_buffer'left downto 8);
						bytes_to_write := bytes_to_write - 1;
						RS232_Tx_start <= '1';
					else
						communicationInstruction <= instructionAfterRS232Transfer;
						RS232_Tx_start <= '0';
					end if;
				else
					RS232_Tx_start <= '0';
				end if;
			when wait_countImmediately =>
				if(
--						asyncResultBufferValid
						asyncCompletionDetected
				) then
					for i in counters'right to counters'left loop
						RS232_Tx_buffer(8*(bytes_to_write+4)-1 downto 8*bytes_to_write)
							:= std_logic_vector(counters(i));
						bytes_to_write := bytes_to_write + 4;
					end loop;
--					if(asyncResultBuffer /= completed) then
--						number_of_counts <= X"FF";
--					end  if;
					communicationInstruction <= wait_rs232_transfer;
				end if;
			when dumpCounterMemory =>
				for i in counters'right to counters'left loop
					RS232_Tx_buffer(8*(bytes_to_write+3)-1 downto 8*bytes_to_write)
						:= std_logic_vector(to_unsigned(0,24
									-triggeredCountingDumpDataOut(i)'length))
							& std_logic_vector(triggeredCountingDumpDataOut(i));
					bytes_to_write := bytes_to_write + 3;
				end loop;
				communicationInstruction <= wait_rs232_transfer;
				if(triggeredCountingDumpAddress < triggeredCountingBins) then
					triggeredCountingDumpAddress <= triggeredCountingDumpAddress + 1;
					instructionAfterRS232Transfer <= dumpCounterMemory;
				else
					triggeredCountingDumpAddress <= triggeredCounting_address_zero;
					instructionAfterRS232Transfer <= wait_rs232_read_instruction;
				end if;
			when resetCounterMemory_init =>
				triggeredCountingDumpAddress <= triggeredCountingBins;
				for i in counters'right to counters'left loop	
--					triggeredCountingDumpDataIn(i) <= to_unsigned(0,triggeredCountingDumpDataIn(i)'length);
					triggeredCountingDumpWriteEnable(i) <= '1';
				end loop;
				communicationInstruction <= resetCounterMemory;
			when resetCounterMemory =>
				if(triggeredCountingDumpAddress = triggeredCounting_address_zero) then
					for i in counters'right to counters'left loop					
						triggeredCountingDumpWriteEnable(i) <= '0';
					end loop;
					communicationInstruction <= wait_rs232_read_instruction;
				else
					triggeredCountingDumpAddress <= triggeredCountingDumpAddress - 1;
				end if;
			when others =>
			end case;
--			bytes_to_read_s <= to_unsigned(bytes_to_read,8);
--			bytes_to_write_s <= to_unsigned(bytes_to_write,8);
			RS232_Rx_busy_last := RS232_Rx_busy;
			RS232_Tx_busy_last := RS232_Tx_busy;
		end if;
	end process;
	
	process(triggeredCountingTrigger,triggeredCountingTriggerAck)
	begin
		if(triggeredCountingTriggerAck = '1') then
			triggeredCountingTriggerBuffer <= '0';
		elsif(RISING_EDGE(triggeredCountingTrigger)) then
			triggeredCountingTriggerBuffer <= '1';
		end if;
	end process;

	process(asyncControlCommandSignal,asyncControlCommandSignalAck)
	begin
		if(asyncControlCommandSignalAck = '1') then
			asyncControlCommandSignalBuffer <= '0';
		elsif(RISING_EDGE(asyncControlCommandSignal)) then
			asyncControlCommandSignalBuffer <= '1';
--			asyncControlCommandBuffer <= asyncControlCommand;
		end if;
	end process;

	process(countClk(0))
		variable triggeredCountingTriggerEdgeDetected			: boolean 	:= false;
		variable counterInstructionBuffer						: counter_instructions	:= idle;
--		variable asyncControlCommandBufferValid					: boolean 	:= false;
		variable asyncControlCommandValid						: boolean 	:= false;
		variable splitTriggeredCountingBinsIndicator			: std_logic	:= '0';
	begin
		if(RISING_EDGE(countClk(0))) then
			if(asyncControlCommandSignalAck = '1') then
				asyncControlCommandSignalAck <= '0';
--				asyncControlCommandBufferValid := true;
				asyncControlCommandValid := true;
			else
				asyncControlCommandSignalAck <= asyncControlCommandSignalBuffer;
--				asyncControlCommandBufferValid := false;
				asyncControlCommandValid := false;
			end if;
			if(triggeredCountingTriggerAck = '1') then
				triggeredCountingTriggerAck <= '0';
				triggeredCountingTriggerEdgeDetected := true;
			else
				triggeredCountingTriggerAck <= triggeredCountingTriggerBuffer;
				triggeredCountingTriggerEdgeDetected := false;
			end if;
--			asyncResult <= none;
			asyncCompletion <= '0';
			counterInstructionBuffer := counterInstruction;
			if(
--					asyncControlCommandBufferValid
					asyncControlCommandValid
			) then
--				case asyncControlCommandBuffer is
				case asyncControlCommand is
				when none =>
				when gotoIdle =>
					counterInstructionBuffer := idle;
				when copyAddress =>
					triggeredCountingWorkAddress <= triggeredCountingDumpAddress;
					triggeredCountingBinRepetitionCounter <=
						to_unsigned(0,triggeredCountingBinRepetitionCounter'length);
					splitTriggeredCountingBinsIndicator := '0';
				when reset =>
					triggeredCountingWorkAddress <= triggeredCounting_address_zero;
					triggeredCountingBinRepetitionCounter <=
						to_unsigned(0,triggeredCountingBinRepetitionCounter'length);
					splitTriggeredCountingBinsIndicator := '0';
					counterInstructionBuffer := idle;
				when countImmediately =>
					counterInstructionBuffer := immediateCounting_start;
				when countTriggered =>
					counterInstructionBuffer := triggeredCounting_waitForTrigger;
				when trigger =>
					triggeredCountingTriggerEdgeDetected := true;
				when others =>
				end case;
			end if;
			counterInstruction <= counterInstructionBuffer;
			case counterInstructionBuffer is
			when idle =>
				counting_stopped <= '1';
				for i in counters'right to counters'left loop
					counters_reset(i) <= '1';
				end loop;
				for i in counters'right to counters'left loop					
					triggeredCountingWorkWriteEnable(i) <= '0';
				end loop;
			when immediateCounting_start =>
				counter_clock <= timeout;
				counting_stopped <= '0';
				for i in counters'right to counters'left loop
					counters_reset(i) <= '0';
				end loop;
				counterInstruction <= immediateCounting_waitForTimeout;
			when immediateCounting_waitForTimeout =>
				if(counter_clock = 0) then
					counting_stopped <= '1';
					for i in counters'right to counters'left loop
						counters_reset(i) <= '1';
					end loop;
--					asyncResult <= completed;
					asyncCompletion <= '1';
					counterInstruction <= idle;
--					debugState <= "00";
				else
					counter_clock <= counter_clock - 1;
--					debugState <= "10";
				end if;
			when triggeredCounting_waitForTrigger =>
				if(triggeredCountingTriggerEdgeDetected) then
					if(enablePredelay) then
						counter_clock <= predelay;
						counterInstruction <= triggeredCounting_predelay;
--						debugState <= "00";
					else
						counter_clock <= timeout;
						counting_stopped <= '0';
						for i in counters'right to counters'left loop
							counters_reset(i) <= '0';
						end loop;
						counterInstruction <= triggeredCounting_waitForTimeout;
--						debugState <= "01";
					end if;
--				else
--					debugState <= "10";
				end if;
			when triggeredCounting_predelay =>
				if(counter_clock = 0) then
					counter_clock <= timeout;
					counting_stopped <= '0';
					for i in counters'right to counters'left loop
						counters_reset(i) <= '0';
					end loop;
					counterInstruction <= triggeredCounting_waitForTimeout;
--					debugState <= "00";
				else
					counter_clock <= counter_clock - 1;
--					debugState <= "10";
				end if;
			when triggeredCounting_waitForTimeout =>
				if(counter_clock = 0) then
					counting_stopped <= '1';
					for i in counters'right to counters'left loop
						counters_reset(i) <= '1';
					end loop;
					counterInstruction <= triggeredCounting_prestore;
--					debugState <= "00";
				else
					counter_clock <= counter_clock - 1;
--					debugState <= "11";
				end if;
			when triggeredCounting_prestore =>
				if splitTriggeredCountingBins then
					if splitTriggeredCountingBinsIndicator = '1' then
						for i in counters'right to counters'left loop
							triggeredCountingWorkDataIn(i) <= 
								(triggeredCountingWorkDataOut(i)(
										triggeredCountingWorkDataOut(i)'length-1 downto
										triggeredCountingWorkDataOut(i)'length/2)
									+ counters(i)(
										triggeredCountingWorkDataOut(i)'length/2-1 downto 0))
								& triggeredCountingWorkDataOut(i)(
									triggeredCountingWorkDataOut(i)'length/2-1 downto 0);
						end loop;
					else
						for i in counters'right to counters'left loop
							triggeredCountingWorkDataIn(i) <= 
								triggeredCountingWorkDataOut(i)(
									triggeredCountingWorkDataOut(i)'length-1 downto
									triggeredCountingWorkDataOut(i)'length/2)
								& (triggeredCountingWorkDataOut(i)(
									triggeredCountingWorkDataOut(i)'length/2-1 downto 0)
									+ counters(i)(
										triggeredCountingWorkDataOut(i)'length/2-1 downto 0));
						end loop;
					end if;
				else
					for i in counters'right to counters'left loop
						triggeredCountingWorkDataIn(i) <= triggeredCountingWorkDataOut(i)
							+ counters(i)(triggeredCountingWorkDataOut(i)'length-1 downto 0);
					end loop;
				end if;
				for i in counters'right to counters'left loop
					triggeredCountingWorkWriteEnable(i) <= '1';
				end loop;
				counterInstruction <= triggeredCounting_store;
			when triggeredCounting_store =>
				for i in counters'right to counters'left loop
					triggeredCountingWorkWriteEnable(i) <= '0';
				end loop;
				if splitTriggeredCountingBins and splitTriggeredCountingBinsIndicator = '0' then
					splitTriggeredCountingBinsIndicator := '1';
				else
					splitTriggeredCountingBinsIndicator := '0';
					if(triggeredCountingBinRepetitionCounter = triggeredCountingBinRepetitions) then
						triggeredCountingBinRepetitionCounter <= 
							to_unsigned(0,triggeredCountingBinRepetitionCounter'length);
						if(triggeredCountingWorkAddress = triggeredCountingBins) then
							triggeredCountingWorkAddress <= triggeredCounting_address_zero;
--						asyncResult <= completed;
							asyncCompletion <= '1';
						else
							triggeredCountingWorkAddress <= triggeredCountingWorkAddress + 1;
						end if;
					else
						triggeredCountingBinRepetitionCounter <= triggeredCountingBinRepetitionCounter + 1;
					end if;
				end if;
				counterInstruction <= triggeredCounting_waitForTrigger;
			when others =>
				counterInstruction <= idle;
			end case;
		end if;
	end process;
end behaviour;	
	
