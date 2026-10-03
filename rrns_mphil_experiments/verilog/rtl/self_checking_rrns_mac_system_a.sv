module self_checking_rrns_mac_system_a #(
    parameter int IN_WIDTH = 8,
    parameter int TAP_COUNT = 9
) (
    input  logic signed [IN_WIDTH-1:0] activations [0:TAP_COUNT-1],
    input  logic signed [IN_WIDTH-1:0] weights     [0:TAP_COUNT-1],
    input  logic       use_fault_override,
    input  logic [4:0] fault_residue_m17,
    input  logic [4:0] fault_residue_m19,
    input  logic [4:0] fault_residue_m23,
    input  logic [4:0] fault_residue_m29,
    output logic signed [15:0] binary_dot_product,
    output logic [4:0] clean_residue_m17,
    output logic [4:0] clean_residue_m19,
    output logic [4:0] clean_residue_m23,
    output logic [4:0] clean_residue_m29,
    output logic [4:0] checked_residue_m17,
    output logic [4:0] checked_residue_m19,
    output logic [4:0] checked_residue_m23,
    output logic [4:0] checked_residue_m29,
    output logic       checker_valid,
    output logic [12:0] reconstructed_unsigned,
    output logic signed [15:0] reconstructed_signed,
    output logic [4:0] predicted_redundant,
    output logic [4:0] syndrome
);

    integer tap;
    int dot_product_int;

    rrns_channel_mac #(
        .MODULUS(17),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(5)
    ) residue_m17_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m17)
    );

    rrns_channel_mac #(
        .MODULUS(19),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(5)
    ) residue_m19_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m19)
    );

    rrns_channel_mac #(
        .MODULUS(23),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(5)
    ) residue_m23_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m23)
    );

    rrns_channel_mac #(
        .MODULUS(29),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(5)
    ) residue_m29_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m29)
    );

    always @* begin
        dot_product_int = 0;
        for (tap = 0; tap < TAP_COUNT; tap = tap + 1) begin
            dot_product_int += $signed(activations[tap]) * $signed(weights[tap]);
        end
        binary_dot_product = dot_product_int[15:0];
    end

    always @* begin
        if (use_fault_override) begin
            checked_residue_m17 = fault_residue_m17;
            checked_residue_m19 = fault_residue_m19;
            checked_residue_m23 = fault_residue_m23;
            checked_residue_m29 = fault_residue_m29;
        end else begin
            checked_residue_m17 = clean_residue_m17;
            checked_residue_m19 = clean_residue_m19;
            checked_residue_m23 = clean_residue_m23;
            checked_residue_m29 = clean_residue_m29;
        end
    end

    rrns_checker_system_a checker_u (
        .residue_m17(checked_residue_m17),
        .residue_m19(checked_residue_m19),
        .residue_m23(checked_residue_m23),
        .residue_m29(checked_residue_m29),
        .checker_valid(checker_valid),
        .reconstructed_unsigned(reconstructed_unsigned),
        .reconstructed_signed(reconstructed_signed),
        .predicted_redundant(predicted_redundant),
        .syndrome(syndrome)
    );

endmodule
