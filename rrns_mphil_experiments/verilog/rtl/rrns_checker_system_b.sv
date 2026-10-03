module rrns_checker_system_b (
    input  logic [5:0] residue_m29,
    input  logic [5:0] residue_m31,
    input  logic [5:0] residue_m37,
    input  logic [5:0] residue_m41,
    output logic       checker_valid,
    output logic [15:0] reconstructed_unsigned,
    output logic signed [15:0] reconstructed_signed,
    output logic [5:0] predicted_redundant,
    output logic [5:0] syndrome
);

    localparam int MR = 41;
    localparam int INFORMATIVE_DYNAMIC_RANGE = 33263;
    localparam int BALANCED_LIMIT = 16631;

    localparam int CRT_COEFF_M29 = 22940;
    localparam int CRT_COEFF_M31 = 19314;
    localparam int CRT_COEFF_M37 = 24273;

    function automatic int signed_mod(input int value, input int modulus);
        int tmp;
        begin
            tmp = value % modulus;
            if (tmp < 0) begin
                tmp = tmp + modulus;
            end
            return tmp;
        end
    endfunction

    int reconstructed_unsigned_int;
    int reconstructed_signed_int;
    int predicted_redundant_int;
    int syndrome_int;

    always @* begin
        reconstructed_unsigned_int =
            ((residue_m29 * CRT_COEFF_M29)
           + (residue_m31 * CRT_COEFF_M31)
           + (residue_m37 * CRT_COEFF_M37)) % INFORMATIVE_DYNAMIC_RANGE;

        if (reconstructed_unsigned_int > BALANCED_LIMIT) begin
            reconstructed_signed_int = reconstructed_unsigned_int - INFORMATIVE_DYNAMIC_RANGE;
        end else begin
            reconstructed_signed_int = reconstructed_unsigned_int;
        end

        predicted_redundant_int = signed_mod(reconstructed_signed_int, MR);
        syndrome_int = signed_mod($signed({1'b0, residue_m41}) - predicted_redundant_int, MR);

        reconstructed_unsigned = reconstructed_unsigned_int[15:0];
        reconstructed_signed = reconstructed_signed_int[15:0];
        predicted_redundant = predicted_redundant_int[5:0];
        syndrome = syndrome_int[5:0];
        checker_valid = (syndrome_int == 0);
    end

endmodule
