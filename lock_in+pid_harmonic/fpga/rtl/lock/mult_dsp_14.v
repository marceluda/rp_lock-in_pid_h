module mult_dsp_14(
    input                    CLK,
    input      signed [13:0] A,
    input      signed [13:0] B,
    output reg signed [27:0] P
);
    always @ (posedge CLK) begin
        P <= A * B;
    end
endmodule

