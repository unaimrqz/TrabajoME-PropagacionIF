#version 330 core

out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D u_state_texture;
uniform vec2 u_grid_size;
uniform ivec2 u_cell_coord;

void main() {
    ivec2 frag = ivec2(floor(TexCoords * u_grid_size));
    vec4 current = texture(u_state_texture, TexCoords);

    if (all(equal(frag, u_cell_coord))) {
        FragColor = vec4(1.0, 0.0, current.b, 1.0);
        return;
    }

    FragColor = current;
}
