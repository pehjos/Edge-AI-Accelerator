module self_checking_rrns_mac_system_b #(
    parameter int IN_WIDTH = 8,
    parameter int TAP_COUNT = 9
) (
    input  logic signed [IN_WIDTH-1:0] activations [0:TAP_COUNT-1],
    input  logic signed [IN_WIDTH-1:0] weights     [0:TAP_COUNT-1],
    input  logic       use_fault_override,
    input  logic [5:0] fault_residue_m29,
    input  logic [5:0] fault_residue_m31,
    input  logic [5:0] fault_residue_m37,
    input  logic [5:0] fault_residue_m41,
    output logic signed [15:0] binary_dot_product,
    output logic [5:0] clean_residue_m29,
    output logic [5:0] clean_residue_m31,
    output logic [5:0] clean_residue_m37,
    output logic [5:0] clean_residue_m41,
    output logic [5:0] checked_residue_m29,
    output logic [5:0] checked_residue_m31,
    output logic [5:0] checked_residue_m37,
    output logic [5:0] checked_residue_m41,
    output logic       checker_valid,
    output logic [15:0] reconstructed_unsigned,
    output logic signed [15:0] reconstructed_signed,
    output logic [5:0] predicted_redundant,
    output logic [5:0] syndrome
);

    integer tap;
    int dot_product_int;

    rrns_channel_mac #(
        .MODULUS(29),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(6)
    ) residue_m29_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m29)
    );

    rrns_channel_mac #(
        .MODULUS(31),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(6)
    ) residue_m31_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m31)
    );

    rrns_channel_mac #(
        .MODULUS(37),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(6)
    ) residue_m37_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m37)
    );

    rrns_channel_mac #(
        .MODULUS(41),
        .IN_WIDTH(IN_WIDTH),
        .TAP_COUNT(TAP_COUNT),
        .OUT_WIDTH(6)
    ) residue_m41_mac (
        .activations(activations),
        .weights(weights),
        .residue_sum(clean_residue_m41)
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
            checked_residue_m29 = fault_residue_m29;
            checked_residue_m31 = fault_residue_m31;
            checked_residue_m37 = fault_residue_m37;
            checked_residue_m41 = fault_residue_m41;
        end else begin
            checked_residue_m29 = clean_residue_m29;
            checked_residue_m31 = clean_residue_m31;
            checked_residue_m37 = clean_residue_m37;
            checked_residue_m41 = clean_residue_m41;
        end
    end

    rrns_checker_system_b checker_u (
        .residue_m29(checked_residue_m29),
        .residue_m31(checked_residue_m31),
        .residue_m37(checked_residue_m37),
        .residue_m41(checked_residue_m41),
        .checker_valid(checker_valid),
        .reconstructed_unsigned(reconstructed_unsigned),
        .reconstructed_signed(reconstructed_signed),
        .predicted_redundant(predicted_redundant),
        .syndrome(syndrome)
    );

endmodule
