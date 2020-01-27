import pyglet
import numpy
import ratcave
import PIL

vert_shader = """
#version 120

attribute vec3 vertexPosition;
attribute vec2 vertexTexcoord;

uniform mat4 projection_matrix, view_matrix, model_matrix;

varying vec2 fragTexCoord;

void main()
{
	gl_Position = projection_matrix * view_matrix * model_matrix * vec4(vertexPosition, 1.0);
	fragTexCoord = vertexTexcoord;
}
"""

frag_shader = """
#version 120

uniform sampler2D TextureMap;

varying vec2 fragTexCoord;

void main()
{
	vec4 color = texture2D(TextureMap, fragTexCoord);
	gl_FragColor = vec4(color.rgb, 1.);
}
"""


def debug_view(vertices, texcoord, image=None, window_size=(800, 600)):
    # creates the window and sets its properties
    width, height = window_size
    window = pyglet.window.Window(width=width,
                                  height=height,
                                  caption='Debug Viewer',
                                  resizable=False)

    num_verts = 3 * vertices.shape[0]
    model = ratcave.Mesh(arrays=(vertices.reshape(num_verts, 3),
                                 texcoord.reshape(num_verts, 2)))
    model.position.xyz = 0, 0, -10

    if image is not None:
        image = image.transpose(PIL.Image.FLIP_TOP_BOTTOM)
        imgdata = pyglet.image.ImageData(image.width, image.height, 'RGBA',
                                         image.tobytes())
        mipmap = False
        tex = imgdata.get_mipmapped_texture(
        ) if mipmap else imgdata.get_texture()
        pyglet.gl.glBindTexture(pyglet.gl.GL_TEXTURE_2D, 0)
        model.textures.append(
            ratcave.Texture(id=tex.id, data=tex, mipmap=mipmap))

    scene = ratcave.Scene(meshes=[model])
    scene.camera.projection = ratcave.PerspectiveProjection(60.0,
                                                            width /
                                                            float(height),
                                                            z_far=100.0)

    def update(dt):
        pass

    pyglet.clock.schedule(update)

    shader = ratcave.Shader(vert=vert_shader, frag=frag_shader)

    @window.event
    def on_resize(width, height):
        # TODO update scene.camera.projection.viewport
        scene.camera.projection.aspect = width / float(height)
        return pyglet.event.EVENT_HANDLED

    @window.event
    def on_draw():
        with shader:
            scene.draw()

    @window.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        # scroll the MOUSE WHEEL to zoom
        scene.camera.position.z -= scroll_y / 10.0

    @window.event
    def on_mouse_drag(x, y, dx, dy, button, modifiers):
        # press the LEFT MOUSE BUTTON to rotate
        if button == pyglet.window.mouse.LEFT:
            model.rotation.y += dx / 5.0
            model.rotation.x -= dy / 5.0

        # press the LEFT and RIGHT MOUSE BUTTONS simultaneously to pan
        if button == pyglet.window.mouse.LEFT | pyglet.window.mouse.RIGHT:
            scene.camera.position.x -= dx / 100.0
            scene.camera.position.y -= dy / 100.0

    # starts the application
    pyglet.app.run()
