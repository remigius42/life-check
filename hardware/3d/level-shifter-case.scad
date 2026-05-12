// Level Shifter Case
//
// A parametric project box for the BSS138-based logic level shifter.
// Optimized for housing the board and Dupont connectors.
//
// Author: Matthew (https://makerworld.com/en/@Matthew)
// Source: https://makerworld.com/en/models/46852
// License: CC-BY (Creative Commons Attribution)
//
// This file was vendored into the Life Check project to provide a
// standard housing for the Raspberry Pi logic level shifter.
//
// Customized with OpenSCAD: https://openscad.org/

//inside dimensions to fit the PCB/etc
inside_x=30;
inside_y=13.5;
inside_z=30;

thickness=1.5; //thickness of walls/bottom (lid is separate)
screw_hole_dia=3; //meant to use a tap to thread after printing
screw_hole_depth=30;

//outside dimensions, leave this alone
outside_x=inside_x+2*thickness+screw_hole_dia+4*thickness;
outside_y=inside_y+2*thickness;

//openings as measured in width (x), height (z), and offset from the left side (x) and bottom (z)
left_opening_x=10;
left_opening_z=3;
left_x_offset=0;
left_z_offset=1;
right_opening_x=0;
right_opening_z=4;
right_x_offset=28;
right_z_offset=1;

//lid
lid_thickness=1.5;
lid_screw_hole_dia=4;

$fn=100;

difference(){
hull(){
translate([-outside_x/2+thickness,outside_y/2-thickness,0])
cylinder(r=thickness,h=inside_z+thickness);
translate([-outside_x/2+thickness,-outside_y/2+thickness])
cylinder(r=thickness,h=inside_z+thickness);
translate([outside_x/2-thickness,outside_y/2-thickness])
cylinder(r=thickness,h=inside_z+thickness);
translate([outside_x/2-thickness,-outside_y/2+thickness])
cylinder(r=thickness,h=inside_z+thickness);
}
translate([0,0,thickness])
hull(){
translate([-outside_x/2+thickness*2,outside_y/2-thickness*2,0])
cylinder(r=thickness,h=inside_z+thickness);
translate([-outside_x/2+thickness*2,-outside_y/2+thickness*2])
cylinder(r=thickness,h=inside_z+thickness);
translate([outside_x/2-thickness*2,outside_y/2-thickness*2])
cylinder(r=thickness,h=inside_z+thickness);
translate([outside_x/2-thickness*2,-outside_y/2+thickness*2])
cylinder(r=thickness,h=inside_z+thickness);
}
translate([-inside_x/2+left_opening_x/2+left_x_offset,-inside_y/2-thickness/2-0.01,thickness+left_z_offset+left_opening_z/2])
cube([left_opening_x,thickness+0.04,left_opening_z],center=true);
translate([-inside_x/2+right_opening_x/2+right_x_offset,-inside_y/2-thickness/2-0.01,thickness+right_z_offset+right_opening_z/2])
cube([right_opening_x,thickness+0.04,right_opening_z],center=true);
}

difference(){
union(){
translate([-outside_x/2+thickness*2,outside_y/2-thickness*2,0])
cylinder(d=thickness*2+screw_hole_dia,h=inside_z+thickness);
translate([-outside_x/2+thickness*2,-outside_y/2+thickness*2])
cylinder(d=thickness*2+screw_hole_dia,h=inside_z+thickness);
translate([outside_x/2-thickness*2,outside_y/2-thickness*2])
cylinder(d=thickness*2+screw_hole_dia,h=inside_z+thickness);
translate([outside_x/2-thickness*2,-outside_y/2+thickness*2])
cylinder(d=thickness*2+screw_hole_dia,h=inside_z+thickness);
}
translate([0,0,inside_z-screw_hole_depth])
union(){
translate([-outside_x/2+thickness*2,outside_y/2-thickness*2,0])
cylinder(d=screw_hole_dia,h=inside_z+thickness);
translate([-outside_x/2+thickness*2,-outside_y/2+thickness*2])
cylinder(d=screw_hole_dia,h=inside_z+thickness);
translate([outside_x/2-thickness*2,outside_y/2-thickness*2])
cylinder(d=screw_hole_dia,h=inside_z+thickness);
translate([outside_x/2-thickness*2,-outside_y/2+thickness*2])
cylinder(d=screw_hole_dia,h=inside_z+thickness);
}
}


translate([0,-outside_y*1.5,0])
difference(){
hull(){
translate([-outside_x/2+thickness,outside_y/2-thickness,0])
cylinder(r=thickness,h=lid_thickness);
translate([-outside_x/2+thickness,-outside_y/2+thickness])
cylinder(r=thickness,h=lid_thickness);
translate([outside_x/2-thickness,outside_y/2-thickness])
cylinder(r=thickness,h=lid_thickness);
translate([outside_x/2-thickness,-outside_y/2+thickness])
cylinder(r=thickness,h=lid_thickness);
}
translate([0,0,-0.01])
{
translate([-outside_x/2+thickness*2,outside_y/2-thickness*2,0])
cylinder(d=lid_screw_hole_dia,h=lid_thickness+0.02);
translate([-outside_x/2+thickness*2,-outside_y/2+thickness*2])
cylinder(d=lid_screw_hole_dia,h=lid_thickness+0.02);
translate([outside_x/2-thickness*2,outside_y/2-thickness*2])
cylinder(d=lid_screw_hole_dia,h=lid_thickness+0.02);
translate([outside_x/2-thickness*2,-outside_y/2+thickness*2])
cylinder(d=lid_screw_hole_dia,h=lid_thickness+0.02);
}}
