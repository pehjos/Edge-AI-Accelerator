module rrns_checker_system_a (
    input  logic [4:0] residue_m17,
    input  logic [4:0] residue_m19,
    input  logic [4:0] residue_m23,
    input  logic [4:0] residue_m29,
    output logic       checker_valid,
    output logic [12:0] reconstructed_unsigned,
    output logic signed [15:0] reconstructed_signed,
    output logic [4:0] predicted_redundant,
    output logic [4:0] syndrome
);

    localparam int M1 = 17;
    localparam int M2 = 19;
    localparam int M3 = 23;
    localparam int MR = 29;
    localparam int INFORMATIVE_DYNAMIC_RANGE = 7429;
    localparam int BALANCED_LIMIT = 3714;

    localparam int CRT_COEFF_M17 = 4370;
    localparam int CRT_COEFF_M19 = 2737;
    localparam int CRT_COEFF_M23 = 323;

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
            ((residue_m17 * CRT_COEFF_M17)
           + (residue_m19 * CRT_COEFF_M19)
           + (residue_m23 * CRT_COEFF_M23)) % INFORMATIVE_DYNAMIC_RANGE;

        if (reconstructed_unsigned_int > BALANCED_LIMIT) begin
            reconstructed_signed_int = reconstructed_unsigned_int - INFORMATIVE_DYNAMIC_RANGE;
        end else begin
            reconstructed_signed_int = reconstructed_unsigned_int;
        end

        predicted_redundant_int = signed_mod(reconstructed_signed_int, MR);
        syndrome_int = signed_mod($signed({1'b0, residue_m29}) - predicted_redundant_int, MR);

        reconstructed_unsigned = reconstructed_unsigned_int[12:0];
        reconstructed_signed = reconstructed_signed_int[15:0];
        predicted_redundant = predicted_redundant_int[4:0];
        syndrome = syndrome_int[4:0];
        checker_valid = (syndrome_int == 0);
    end

endmodule
