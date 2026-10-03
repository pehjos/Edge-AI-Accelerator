`timescale 1ns/1ps

module tb_self_checking_rrns_mac_system_a;

    localparam int TAP_COUNT = 9;
    localparam int IN_WIDTH = 8;

    logic signed [IN_WIDTH-1:0] activations [0:TAP_COUNT-1];
    logic signed [IN_WIDTH-1:0] weights     [0:TAP_COUNT-1];
    logic       use_fault_override;
    logic [4:0] fault_residue_m17;
    logic [4:0] fault_residue_m19;
    logic [4:0] fault_residue_m23;
    logic [4:0] fault_residue_m29;
    logic signed [15:0] binary_dot_product;
    logic [4:0] clean_residue_m17;
    logic [4:0] clean_residue_m19;
    logic [4:0] clean_residue_m23;
    logic [4:0] clean_residue_m29;
    logic [4:0] checked_residue_m17;
    logic [4:0] checked_residue_m19;
    logic [4:0] checked_residue_m23;
    logic [4:0] checked_residue_m29;
    logic       checker_valid;
    logic [12:0] reconstructed_unsigned;
    logic signed [15:0] reconstructed_signed;
    logic [4:0] predicted_redundant;
    logic [4:0] syndrome;

    int pass_count;
    int fail_count;
    int tap;

    self_checking_rrns_mac_system_a #(
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT)
    ) dut (
        .activations(activations),
        .weights(weights),
        .use_fault_override(use_fault_override),
        .fault_residue_m17(fault_residue_m17),
        .fault_residue_m19(fault_residue_m19),
        .fault_residue_m23(fault_residue_m23),
        .fault_residue_m29(fault_residue_m29),
        .binary_dot_product(binary_dot_product),
        .clean_residue_m17(clean_residue_m17),
        .clean_residue_m19(clean_residue_m19),
        .clean_residue_m23(clean_residue_m23),
        .clean_residue_m29(clean_residue_m29),
        .checked_residue_m17(checked_residue_m17),
        .checked_residue_m19(checked_residue_m19),
        .checked_residue_m23(checked_residue_m23),
        .checked_residue_m29(checked_residue_m29),
        .checker_valid(checker_valid),
        .reconstructed_unsigned(reconstructed_unsigned),
        .reconstructed_signed(reconstructed_signed),
        .predicted_redundant(predicted_redundant),
        .syndrome(syndrome)
    );

    task automatic clear_inputs;
        begin
            for (tap = 0; tap < TAP_COUNT; tap = tap + 1) begin
                activations[tap] = '0;
                weights[tap] = '0;
            end
            use_fault_override = 1'b0;
            fault_residue_m17 = '0;
            fault_residue_m19 = '0;
            fault_residue_m23 = '0;
            fault_residue_m29 = '0;
        end
    endtask

    task automatic load_single_product_case;
        begin
            clear_inputs();
            activations[0] = -8'sd10;
            weights[0] = 8'sd20;
        end
    endtask

    task automatic load_multi_tap_case;
        begin
            clear_inputs();
            activations[0] =  8'sd2;  weights[0] = -8'sd4;
            activations[1] =  8'sd6;  weights[1] =  8'sd7;
            activations[2] =  8'sd1;  weights[2] =  8'sd5;
            activations[3] = -8'sd6;  weights[3] = -8'sd7;
            activations[4] = -8'sd5;  weights[4] = -8'sd6;
            activations[5] =  8'sd8;  weights[5] =  8'sd2;
            activations[6] =  8'sd5;  weights[6] =  8'sd2;
            activations[7] = -8'sd3;  weights[7] =  8'sd3;
            activations[8] =  8'sd2;  weights[8] =  8'sd7;
        end
    endtask

    task automatic check_equal_int(input string label, input int observed, input int expected);
        begin
            if (observed !== expected) begin
                $display("FAIL: %s observed=%0d expected=%0d", label, observed, expected);
                fail_count = fail_count + 1;
            end else begin
                $display("PASS: %s observed=%0d", label, observed);
                pass_count = pass_count + 1;
            end
        end
    endtask

    task automatic check_equal_bit(input string label, input logic observed, input logic expected);
        begin
            if (observed !== expected) begin
                $display("FAIL: %s observed=%0b expected=%0b", label, observed, expected);
                fail_count = fail_count + 1;
            end else begin
                $display("PASS: %s observed=%0b", label, observed);
                pass_count = pass_count + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("verilog/waveforms/tb_self_checking_rrns_mac_system_a.vcd");
        $dumpvars(0, tb_self_checking_rrns_mac_system_a);

        pass_count = 0;
        fail_count = 0;

        $display("---- Case 1: clean single-product MAC ----");
        load_single_product_case();
        #1;
        check_equal_int("binary dot product", binary_dot_product, -200);
        check_equal_int("clean residue m17", clean_residue_m17, 4);
        check_equal_int("clean residue m19", clean_residue_m19, 9);
        check_equal_int("clean residue m23", clean_residue_m23, 7);
        check_equal_int("clean residue m29", clean_residue_m29, 3);
        check_equal_bit("clean checker valid", checker_valid, 1'b1);
        check_equal_int("clean reconstructed signed", reconstructed_signed, -200);
        check_equal_int("predicted redundant residue", predicted_redundant, 3);

        $display("---- Case 2: detected single informative-channel fault ----");
        use_fault_override = 1'b1;
        fault_residue_m17 = 5;
        fault_residue_m19 = clean_residue_m19;
        fault_residue_m23 = clean_residue_m23;
        fault_residue_m29 = clean_residue_m29;
        #1;
        check_equal_bit("single informative fault detected", checker_valid, 1'b0);

        $display("---- Case 3: detected single redundant-channel fault ----");
        fault_residue_m17 = clean_residue_m17;
        fault_residue_m19 = clean_residue_m19;
        fault_residue_m23 = clean_residue_m23;
        fault_residue_m29 = 4;
        #1;
        check_equal_bit("single redundant fault detected", checker_valid, 1'b0);
        check_equal_int("redundant fault keeps reconstructed signed value", reconstructed_signed, -200);

        $display("---- Case 4: undetected two-informative fault example ----");
        fault_residue_m17 = 5;
        fault_residue_m19 = 1;
        fault_residue_m23 = 7;
        fault_residue_m29 = 3;
        #1;
        check_equal_bit("undetected two-channel fault remains checker-valid", checker_valid, 1'b1);
        check_equal_int("undetected two-channel reconstructed value", reconstructed_signed, -2868);

        $display("---- Case 5: clean multi-tap MAC window ----");
        load_multi_tap_case();
        #1;
        check_equal_int("multi-tap binary dot product", binary_dot_product, 142);
        check_equal_int("multi-tap residue m17", clean_residue_m17, 6);
        check_equal_int("multi-tap residue m19", clean_residue_m19, 9);
        check_equal_int("multi-tap residue m23", clean_residue_m23, 4);
        check_equal_int("multi-tap residue m29", clean_residue_m29, 26);
        check_equal_bit("multi-tap checker valid", checker_valid, 1'b1);
        check_equal_int("multi-tap reconstructed signed", reconstructed_signed, 142);

        $display("---- Testbench summary ----");
        $display("PASS COUNT = %0d", pass_count);
        $display("FAIL COUNT = %0d", fail_count);

        if (fail_count != 0) begin
            $fatal(1, "RRNS MAC/checker testbench failed.");
        end

        $finish;
    end

endmodule
