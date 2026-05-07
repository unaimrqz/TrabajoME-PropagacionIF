// vertex.glsl
// Este es el shader de vértices, que es la etapa inicial del pipeline de renderizado.
// Su función principal es transformar las coordenadas de los vértices de la cuadrícula
// en coordenadas de pantalla. En este caso, como estamos renderizando una cuadrícula
// que ocupa toda la pantalla, simplemente transformamos las coordenadas de los vértices
// de un rango de [-1, 1] a un rango de [0, 1] para las coordenadas de textura, y dejamos
// las coordenadas de posición sin cambios para que la cuadrícula ocupe toda la pantalla.


#version 330 core

in vec2 aPos;
out vec2 TexCoords;

void main() {
    TexCoords = aPos * 0.5 + 0.5;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
