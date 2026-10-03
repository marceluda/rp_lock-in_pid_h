`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
//
// Protección contra saturación.
//
// A menudo se recortan un bus de datos para adaptarlo a otro. satprotect permite
// realizar ese empalme teniendo en cuenta los bits que se descartan para
// saturar la salida cuando sea necesario
//
//////////////////////////////////////////////////////////////////////////////////

/* Descripción:

Parámetros:

  - Ri  : resolucion de la entrada en bits
  - Ro  : resolucion de la salida en bits


*/


//(* keep_hierarchy = "yes" *)
module satprotect2 #(
   parameter     Ri  = 15,
   parameter     Ro  = 14
   )
(
    //input clk,rst,
    input  signed [Ri-1:0] in,    // input signal
    output signed [Ro-1:0] out    // output signal
    );

    wire pos_sat, neg_sat;

    generate
	  if (Ro<Ri-1)
		begin
			assign pos_sat = ( ~in[Ri-1] ) & (     |in[Ri-2:Ro-1]  );
			assign neg_sat = (  in[Ri-1] ) & ( ~ ( &in[Ri-2:Ro-1] ) );
		end else begin
			assign pos_sat = ( ~in[Ri-1] ) & (     in[Ri-2]  );
			assign neg_sat = (  in[Ri-1] ) & ( ~   in[Ri-2]  );
	  end
	endgenerate

    generate
      if (Ri<Ro)
        assign out = (pos_sat|neg_sat) ? { in[Ri-1] , {1'b1{in[Ri-1]}} , {Ro-2{~in[Ri-1]}} }  :  in[Ro-1:0] ;
      else
        assign out = (pos_sat|neg_sat) ? { in[Ri-1] , {Ro-1{~in[Ri-1]}} }  :  in[Ro-1:0] ;
    endgenerate

endmodule

/*
Instantiation example:

satprotect #(.Ri(15),.Ro(14),.SAT(14)) i_satprotect ( .in(IN), .out(OUT) );


*/
