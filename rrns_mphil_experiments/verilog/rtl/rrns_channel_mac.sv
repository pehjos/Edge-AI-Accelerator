module rrns_channel_mac #(
    parameter int MODULUS = 17,
    parameter int IN_WIDTH = 8,
    parameter int TAP_COUNT = 9,
    parameter int OUT_WIDTH = $clog2(MODULUS)
) (
    input  logic signed [IN_WIDTH-1:0] activations [0:TAP_COUNT-1],
    input  logic signed [IN_WIDTH-1:0] weights     [0:TAP_COUNT-1],
    output logic        [OUT_WIDTH-1:0] residue_sum
);

    function automatic int signed_mod(input int value);
        int tmp;
        begin
            tmp = value % MODULUS;
            if (tmp < 0) begin
                tmp = tmp + MODULUS;
            end
            return tmp;
        end
    endfunction

    integer tap;
    int residue_accum;
    int a_residue;
    int w_residue;

    always @* begin
        residue_accum = 0;
        for (tap = 0; tap < TAP_COUNT; tap = tap + 1) begin
            a_residue = signed_mod($signed(activations[tap]));
            w_residue = signed_mod($signed(weights[tap]));
            residue_accum = signed_mod(residue_accum + (a_residue * w_residue));
        end
        residue_sum = residue_accum[OUT_WIDTH-1:0];
    end

endmodule
