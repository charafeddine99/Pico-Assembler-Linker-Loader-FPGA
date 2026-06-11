module top (
    input clk,
    input reset_n,
    input uart_rx_pin,
    output reg [5:0] led
);
    // --------------------------------------------------------
    // 1. GÜVENLİ RESET VE UART BAĞLANTISI
    // --------------------------------------------------------
    reg [15:0] reset_counter = 0;
    wire internal_resetn = (reset_counter == 16'hFFFF) & reset_n;

    always @(posedge clk) begin
        if (!reset_n) reset_counter <= 0;
        else if (reset_counter < 16'hFFFF) reset_counter <= reset_counter + 1;
    end

    wire [7:0] rx_data;
    wire rx_valid;

    uart_rx receiver (
        .clk(clk),
        .reset_n(internal_resetn),
        .rx(uart_rx_pin),
        .rx_data(rx_data),
        .rx_valid(rx_valid)
    );

    // --------------------------------------------------------
    // 2. LOADER FSM (DÜZELTİLMİŞ & GÜVENLİ)
    // --------------------------------------------------------
    reg cpu_run = 0; 
    reg [2:0] byte_count = 0; // 0-3 Veri, 4 Checksum
    reg [31:0] assembled_word = 0;
    reg [7:0] calculated_checksum = 0;
    reg [31:0] loader_addr = 0;
    reg loader_write = 0;
    reg [23:0] timeout_ctr = 0;

    always @(posedge clk) begin
        loader_write <= 0; // Default olarak RAM yazmayı kapalı tut

        if (!internal_resetn) begin
            cpu_run             <= 0;
            byte_count          <= 0;
            loader_addr         <= 0;
            timeout_ctr         <= 0;
            calculated_checksum <= 0;
            assembled_word      <= 0;
        end else if (!cpu_run) begin
            
            if (rx_valid) begin
                timeout_ctr <= 0; // Her yeni veri geldiğinde zamanlayıcıyı sıfırla
                
                if (byte_count < 4) begin
                    // İlk byte gelmişse checksum'ı direkt ona eşitle, yoksa XOR'lamaya devam et
                    if (byte_count == 0)
                        calculated_checksum <= rx_data;
                    else
                        calculated_checksum <= calculated_checksum ^ rx_data;
                        
                    assembled_word[byte_count*8 +: 8] <= rx_data;
                    byte_count <= byte_count + 1;
                end else begin
                    // 5. bayt geldi: Checksum kontrolü
                    if (rx_data == calculated_checksum) begin
                        loader_write <= 1; // RAM'e yazma sinyalini ateşle
                    end
                    byte_count <= 0;
                    // Bir sonraki paket için checksum burada sıfırlanmamalı, 
                    // yeni paketin 0. byte'ında set edilmeli.
                end
            end 
            
            // BUG DÜZELTMESİ: Yazma sinyali aktifleştikten bir sonraki saat çevriminde 
            // adresi güvenli bir şekilde artırıyoruz (rx_valid'den bağımsız çalışmalı).
            if (loader_write) begin
                loader_addr <= loader_addr + 4;
            end 
            
            // Eğer RAM'e en az 1 paket yazıldıysa ve artık UART hattı sessizse timeout saymaya başla
            if (loader_addr > 0 && !rx_valid && !loader_write) begin
                if (timeout_ctr < 24'd17_500_000) 
                    timeout_ctr <= timeout_ctr + 1;
                else
                    cpu_run <= 1; // Belirlenen süre boyunca veri gelmedi, CPU'yu başlat!
            end
        end
    end

    // --------------------------------------------------------
    // 3. PİCORV32 İŞLEMCİ ÇEKİRDEĞİ
    // --------------------------------------------------------
    wire mem_valid;
    reg  mem_ready;
    wire [31:0] mem_addr, mem_wdata;
    wire [3:0] mem_wstrb;
    reg  [31:0] mem_rdata;

    wire cpu_reset_pin = internal_resetn & cpu_run;

    picorv32 cpu (
        .clk(clk),
        .resetn(cpu_reset_pin),
        .mem_valid(mem_valid),
        .mem_ready(mem_ready),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_wstrb(mem_wstrb),
        .mem_rdata(mem_rdata)
    );

    // --------------------------------------------------------
    // 4. BRAM MİMARİSİ
    // --------------------------------------------------------
    reg [7:0] mem_b0 [0:1023];
    reg [7:0] mem_b1 [0:1023];
    reg [7:0] mem_b2 [0:1023];
    reg [7:0] mem_b3 [0:1023];

    wire [9:0] ram_addr   = (!cpu_run) ? loader_addr[11:2] : mem_addr[11:2];
    wire [31:0] ram_wdata = (!cpu_run) ? assembled_word : mem_wdata;

    wire we_loader = (!cpu_run && loader_write);
    wire we_cpu    = (cpu_run && mem_valid && !mem_ready && (mem_addr != 32'd128));

    wire [3:0] ram_wen;
    assign ram_wen[0] = we_loader | (we_cpu & mem_wstrb[0]);
    assign ram_wen[1] = we_loader | (we_cpu & mem_wstrb[1]);
    assign ram_wen[2] = we_loader | (we_cpu & mem_wstrb[2]);
    assign ram_wen[3] = we_loader | (we_cpu & mem_wstrb[3]);

    always @(posedge clk) begin
        if (ram_wen[0]) mem_b0[ram_addr] <= ram_wdata[7:0];
        if (ram_wen[1]) mem_b1[ram_addr] <= ram_wdata[15:8];
        if (ram_wen[2]) mem_b2[ram_addr] <= ram_wdata[23:16];
        if (ram_wen[3]) mem_b3[ram_addr] <= ram_wdata[31:24];

        mem_rdata <= {mem_b3[ram_addr], mem_b2[ram_addr], mem_b1[ram_addr], mem_b0[ram_addr]};
    end

    // --------------------------------------------------------
    // 5. LED BLOĞU
    // --------------------------------------------------------
    always @(posedge clk) begin
        if (!internal_resetn) begin
            led <= 6'b111111;
            mem_ready <= 0;
        end else if (cpu_run) begin
            mem_ready <= 0;
            if (mem_valid && !mem_ready) begin
                mem_ready <= 1;
                if (|mem_wstrb && (mem_addr == 32'd128)) begin
                    led[5:0] <= ~mem_wdata[5:0];
                end
            end
        end
    end
endmodule