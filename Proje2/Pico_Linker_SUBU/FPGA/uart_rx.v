module uart_rx #(
    // Tang Nano 9K'nın 27 MHz saati için 115200 Baud Rate hesaplaması:
    // 27.000.000 / 115200 = 234.375 -> Yuvarlarsak 234
    parameter CLKS_PER_BIT = 234
)(
    input clk,
    input reset_n,
    input rx,
    output reg [7:0] rx_data,
    output reg rx_valid
);

    localparam s_IDLE    = 3'b000;
    localparam s_START   = 3'b001;
    localparam s_DATA    = 3'b010;
    localparam s_STOP    = 3'b011;
    localparam s_CLEANUP = 3'b100;

    reg [2:0] state = s_IDLE;
    reg [15:0] clock_count = 0;
    reg [2:0] bit_index = 0;
    reg [7:0] data_reg = 0;

    always @(posedge clk) begin
        if (!reset_n) begin
            state <= s_IDLE;
            clock_count <= 0;
            bit_index <= 0;
            rx_data <= 0;
            rx_valid <= 0;
        end else begin
            case (state)
                s_IDLE: begin
                    rx_valid <= 0;
                    clock_count <= 0;
                    bit_index <= 0;
                    if (rx == 1'b0) // Başlangıç (Start) biti yakalandı! Hattın 0'a inmesi
                        state <= s_START;
                end

                s_START: begin
                    // Bitin tam ortasına gelene kadar bekle ki parazit okumayalım
                    if (clock_count == (CLKS_PER_BIT-1)/2) begin
                        if (rx == 1'b0) begin
                            clock_count <= 0;
                            state <= s_DATA;
                        end else begin
                            state <= s_IDLE; // Yanlış alarm
                        end
                    end else begin
                        clock_count <= clock_count + 1;
                    end
                end

                s_DATA: begin
                    // Her bir veri biti için 1 tam periyot (234 saat vuruşu) bekle
                    if (clock_count < CLKS_PER_BIT-1) begin
                        clock_count <= clock_count + 1;
                    end else begin
                        clock_count <= 0;
                        data_reg[bit_index] <= rx; // Hattaki değeri kaydet
                        
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 1;
                        end else begin
                            bit_index <= 0;
                            state <= s_STOP;
                        end
                    end
                end

                s_STOP: begin
                    // Bitiş (Stop) biti beklemesi
                    if (clock_count < CLKS_PER_BIT-1) begin
                        clock_count <= clock_count + 1;
                    end else begin
                        rx_data <= data_reg;  // Toplanan 8 biti dışarı ver
                        rx_valid <= 1'b1;     // Veri hazır bayrağını kaldır!
                        clock_count <= 0;
                        state <= s_CLEANUP;
                    end
                end

                s_CLEANUP: begin
                    rx_valid <= 1'b0; // Bayrağı hemen indir ki çift tetikleme yapmasın
                    state <= s_IDLE;
                end
                
                default: state <= s_IDLE;
            endcase
        end
    end
endmodule