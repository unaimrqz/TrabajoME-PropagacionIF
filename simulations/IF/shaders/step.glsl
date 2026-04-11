// step.glsl

/*
GLSL es la innovación clave que permite que toda la simulación se ejecute en la GPU. 
Este usa una sintaxis similar a C, pero con funciones y tipos de datos específicos 
para gráficos. El concepto clave en GLSL es que cada fragmento (pixel) se procesa de 
forma independiente, lo que permite que la simulación se ejecute en paralelo en miles 
de núcleos de la GPU, lo que hace que la simulación sea extremadamente rápida incluso
para cuadrículas grandes. Es muy importante entender que en GLSL no hay bucles 
tradicionales ni acceso a memoria global como en otros lenguajes de programación, 
sino que cada fragmento solo puede acceder a su propia información y a la información
de sus vecinos a través de texturas. Esto requiere un enfoque diferente para implementar
la lógica de la simulación, pero también es lo que permite que la simulación sea tan 
eficiente. Nos referimos como shader a cada programa GLSL que se ejecuta en la GPU, y 
cada shader tiene una función main() que es el punto de entrada para cada fragmento que 
se procesa. En este shader es donde se implementa la lógica de propagación del fuego, y 
se actualiza el estado de cada célula en función de su estado actual, el estado de sus 
vecinos, la influencia del viento y la elevación del terreno.
*/

// Este shader es el núcleo de la simulación. Aquí es donde se implementa la lógica 
// de propagación del fuego. Cada vez que se ejecuta este shader, se calcula el nuevo 
// estado de cada célula en función de su estado actual, el estado de sus vecinos, 
// la influencia del viento, y la elevación del terreno. Este shader se ejecuta en cada 
// frame de la simulación, y actualiza la textura de estado que se utiliza para renderizar 
// la cuadrícula. La lógica de propagación se basa en un modelo SIR modificado para incluir 
// factores como el viento y la elevación, y también incluye la posibilidad de que las
// células ardiendo lancen pavesas que puedan iniciar nuevos focos de incendio en otras 
// partes de la cuadrícula.

#version 330 core          // especificamos la versión de GLSL que estamos utilizando

// Algo clave en glsl es el uso de vec2, vec3, vec4 para representar vectores de 2, 3 o 4 
// componentes. Aquí usamos vec4 para representar el estado de cada célula (fuego, elevación,
// combustible, opacidad) y vec2 para coordenadas y tamaños. Out es para enviar datos al 
// siguiente etapa del pipeline de renderizado. In es para recibir datos de la etapa anterior
// (en este caso, las coordenadas de textura).
out vec4 FragColor;        
in vec2 TexCoords;

// Ahora defnimos variables uniformes. Toman los valores que se les asignan desde el programa principal en Python.
uniform sampler2D u_texture;
uniform vec2 u_grid_size;
uniform vec2 u_wind;
uniform float u_time;
uniform float u_pavesas_prob;
uniform float u_beta;
uniform float u_gamma;

// Definiremos la función rand para generar números aleatorios en GLSL:
// Esta forma de generar números aleatorios es común en GLSL, ya que no hay una función de 
// generación de números aleatorios incorporada. Se basa en una función trigonométrica y la
// función fract para generar un valor pseudoaleatorio a partir de las coordenadas de textura
// y el tiempo, lo que permite que el comportamiento del fuego sea impredecible pero reproducible.

//Aunque usamos rand en python para generar variaciones de viento, también lo usamos aquí 
//para generar variaciones en la ignición del fuego, lo que hace que la simulación sea más 
//realista y menos determinista. En caso de no haber usado rand, el fuego se propagaría de 
//manera completamente predecible, lo que no es realista para un fenómeno tan caótico como 
//un incendio forestal.

float rand(vec2 co){ return fract(sin(dot(co, vec2(12.9898, 78.233)) + u_time) * 43758.5453); }



void main() {
    vec2 px = 1.0 / u_grid_size; // ¿Por qué dividimso 1.0 por el tamaño de la cuadrícula? 
                                 // Porque en GLSL las coordenadas de textura van de 0.0 a 1.0,
                                 // y cada célula ocupa un espacio proporcional a su tamaño 
                                 // dentro de esa unidad. Por ejemplo, si la cuadrícula es de 
                                 // 100x100, cada célula ocupará un espacio de 0.01 en las 
                                 // coordenadas de textura, por lo que el desplazamiento para 
                                 // acceder a los vecinos será de 1.0 / grid_size.


    vec2 uv_coords = TexCoords;  // Recordemos que TexCoords son las coordenadas de textura para 
                                 //el fragmento actual, que van de 0.0 a 1.0 a lo largo de la 
                                 // cuadrícula. Estas coordenadas se utilizan para acceder al 
                                 //estado actual de la célula correspondiente en la textura de 
                                 //estado, y también para calcular las coordenadas de los 
                                 //vecinos. Recordemos que en la compilación de shaders GLSL
                                 // cada fragmento se procesa de forma independiente, por lo
                                 // que cuando nos referimos a TexCoords, no nos hace falta 
                                 // especificar a qué célula nos referimos, porque cada una se
                                 // procesará sincronizadamente con su propia coordenada de textura.
                                

    vec4 color = texture(u_texture, uv_coords);
    float fire = color.r;
    float fuel = color.b;
    float my_elev = color.g;

    // Consumo gamma: si hay fuego, se consume combustible.
    if (fire > 0.0) {
        fuel -= u_gamma;
        if (fuel <= 0.0) {
            fuel = 0.0;
            fire -= 0.1;
        }
    }

    // Contagio beta: celda susceptible recibe calor de vecinos.
    if (fire == 0.0 && fuel > 0.0) {
        float heat = 0.0;

        // Ahora viene la parte más interesante: el cálculo del calor que recibe cada 
        // célula de sus vecinos. Lo hacemos con un doble bucle for:
        // Este doble bucle recorre los 8 vecinos de la célula actual (y a sí misma, 
        // aunque se salta esa parte) para calcular el calor total que recibe la célula.
        // El calor se calcula en función del estado de fuego de cada vecino, la influencia 
        // del viento (que hace que el calor sea mayor si viene del lado del viento), y la
        // pendiente del terreno (que hace que el calor sea mayor si la célula actual está 
        // por debajo de sus vecinos). Este enfoque permite que la simulación tenga un 
        // comportamiento más realista, ya que el fuego se propaga más fácilmente en 
        // dirección del viento y cuesta más propagarse cuesta arriba. En un modelo SIR 
        // tradicional, solo se consideraría el estado de los vecinos para determinar la 
        // probabilidad de contagio, pero aquí hemos añadido estos factores adicionales 
        // para hacer la simulación más rica e interesante. Es clave entender que en glsl
        // las coordenadas x e y del bucle representan el desplazamiento respecto a la célula
        // actual, por lo que x=-1, y=-1 representa el vecino superior izquierdo, x=0, y=-1 
        // representa el vecino superior, x=1, y=-1 representa el vecino superior derecho, y 
        // así sucesivamente. El numero de celulas total será u_grid_size.x * u_grid_size.y, 
        // pero cada célula solo puede acceder a su propio estado y al estado de sus vecinos 
        // a través de la textura, lo que es lo que permite que la simulación se ejecute en
        // paralelo en la GPU.

        for (int y = -1; y <= 1; y++) { // La interacción es a primeros vecinos.
            for (int x = -1; x <= 1; x++) {
                if (x == 0 && y == 0) {
                    continue;
                }

                // Sacamos coordenadas y estado del vecino
                vec2 offset = vec2(float(x), float(y));                 // desplazamiento del vecino respecto a la célula actual
                vec2 neighbor_uv = uv_coords - offset * px;             // coordenadas de textura del vecino
                vec4 neighbor = texture(u_texture, neighbor_uv);        // estado del vecino 
                float neighbor_fire = neighbor.r;                       // estado de fuego del vecino. (neightbor.r o texture(u_texture, neighbor_uv).r es para acceder al canal rojo de la textura, que es donde guardamos el estado de fuego
                
                // Influencia de la pendiente
                float nb_elev = texture(u_texture, neighbor_uv).g;      // elevación del vecino. (lo de .g es para acceder al canal verde de la textura, que es donde guardamos la elevación)
                float slope = my_elev - nb_elev;                        // pendiente entre la célula actual y el vecino. Si es positiva, la célula actual está por encima del vecino, lo que hace que el fuego se propague más fácilmente. Si es negativa, la célula actual está por debajo del vecino, lo que hace que el fuego se propague con más dificultad.
                float slope_factor = max(0.0, (slope / px.x) * 2.0);    // A REVISAR: Quizá convenga añadir el factor de escala en main window y reformular esto de la pendiente.

                // Influencia del viento
                float wind_factor = max(0.0, dot(normalize(offset), u_wind));   // El factor de viento se calcula como el producto escalar entre la dirección del vecino (offset) y la dirección del viento (u_wind). Esto hace que el calor sea mayor si el vecino está en la dirección del viento, y menor si está en contra del viento.
                
                // Acumulamos el calor recibido de este vecino, que es proporcional a su estado de fuego, y se ve amplificado por la influencia del viento y la pendiente.
                heat += neighbor_fire * (1.0 + wind_factor) * (1.0 + slope_factor); 
            }
        }


        // Finalmente, calculamos la probabilidad de ignición en función del calor total 
        // recibido, y decidimos si la célula se enciende o no. La probabilidad de ignición 
        // se calcula como una función del calor recibido multiplicado por un factor de 
        // contagio u_beta, lo que hace que el fuego se propague más fácilmente si el calor 
        // es alto. Luego generamos un número aleatorio entre 0 y 1, y si es menor que la 
        // probabilidad de ignición, encendemos la célula (fire = 1.0). Esto introduce un elemento de aleatoriedad en la propagación del fuego, lo que hace que la simulación sea más realista e impredecible.
        float ignition_prob = clamp(heat * 0.1 * u_beta, 0.0, 1.0);
        float random_val = rand(uv_coords + fract(u_time * 0.123)); 
        if (random_val < ignition_prob) {
            fire = 1.0;
        }

// - PAVESAS: Limpio, directo y con probabilidad real --------------------------------
        if (u_pavesas_prob > 1e-5) {
            float w_len = length(u_wind);
            
            // 1. Solo evaluamos si hay viento (tuyo)
            if (w_len > 0.1) {
                vec2 wind_dir = normalize(u_wind);
                
                // 2. EL DADO ARREGLADO: Tu función rand() de arriba ya usa u_time por dentro. 
                // Solo necesitamos sumarle números fijos diferentes para que el ángulo, 
                // la distancia y la suerte no compartan el mismo número aleatorio. ¡Cero agrupaciones!
                float r1 = rand(uv_coords + vec2(1.23, 4.56)); // Para el ángulo
                float r2 = rand(uv_coords + vec2(7.89, 1.23)); // Para la distancia
                float r3 = rand(uv_coords + vec2(3.45, 6.78)); // El dado de la probabilidad
                
                // 3. Ángulo de dispersión (entre -0.525 y 0.525 radianes, es decir, ±30 grados)
                float angle_noise = (r1 - 0.5) * 1.05;
                float cos_a = cos(angle_noise);
                float sin_a = sin(angle_noise);
                vec2 scatter_dir = vec2(wind_dir.x * cos_a - wind_dir.y * sin_a, wind_dir.x * sin_a + wind_dir.y * cos_a);
                
                // 4. Distancia de salto (del 15% al 55% de la pantalla)
                float dist_noise = 0.15 + (r2 * 0.4); 
                vec2 upwind_uv = uv_coords - (scatter_dir * dist_noise);
                
                if (upwind_uv.x >= 0.0 && upwind_uv.x <= 1.0 && upwind_uv.y >= 0.0 && upwind_uv.y <= 1.0) {
                    vec4 upwind_cell = texture(u_texture, upwind_uv);
                    
                    // 5. LA CONDICIÓN FÍSICA: 
                    if (upwind_cell.r > 0.98 && upwind_cell.b > 0.15) {
                        
                        // 6. Tiramos el dado.
                        if (r3 < u_pavesas_prob) {
                            fire = 0.1;
                        }
                    }
                }
            }
        }
    }

    fire = clamp(fire, 0.0, 1.0);
    fuel = clamp(fuel, 0.0, 1.0);

    FragColor = vec4(fire, my_elev, fuel, 1.0);
}

