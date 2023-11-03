import gradio as gr
from phue import Bridge

# save groups as a .json file, so you can inspect the structure
# only for debug purposes
# with open('groups.json', 'w') as f:
    # json.dump(groups, f, indent=4)

def get_lights(ip):

    # Connect to Philips Hue bridge
    b = Bridge(ip=ip)
    b.connect()

    # get its lights
    lights = b.get_light_objects('name')
    groups = b.get_group()

    # Convert light IDs to names for lookup
    light_id_to_name = {light.light_id: name for name, light in lights.items()}

    # Organize lights under their respective groups
    grouped_lights = {}
    for group_id, group in groups.items():
        group_lights = []
        for light_id in group["lights"]:
            # Convert light ID to light name
            light_name = light_id_to_name.get(int(light_id))
            if light_name:
                group_lights.append(light_name)
        grouped_lights[group["name"]] = group_lights

    # sort lights by name
    grouped_lights[group["name"]].sort()

    return lights, groups, grouped_lights

def rgb_to_xy(red, green, blue):
    # Convert RGB to 0-1 range
    r = red / 255.0
    g = green / 255.0
    b = blue / 255.0

    # Apply gamma correction
    r = ((r + 0.055) / (1.0 + 0.055)) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / (1.0 + 0.055)) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / (1.0 + 0.055)) ** 2.4 if b > 0.04045 else b / 12.92

    # Convert to XYZ space
    X = r * 0.664511 + g * 0.154324 + b * 0.162028
    Y = r * 0.283881 + g * 0.668433 + b * 0.047685
    Z = r * 0.000088 + g * 0.072310 + b * 0.986039

    # Convert to xy space
    if X + Y + Z == 0:
        return 0, 0  # Black, or an approximation
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)

    return x, y

def hex_to_rgb(hex_color):
    # Convert HEX color to RGB tuple
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def control_lightstrip(lights, light_name, hex_color):
    light = lights.get(light_name)
    if light is None:
        return "Light not found"

    # Convert HEX to RGB, then RGB to xy
    rgb = hex_to_rgb(hex_color)
    xy = rgb_to_xy(*rgb)
    light.xy = xy

    return f"Color of {light_name} set to {rgb}"

import gradio as gr
from phue import Bridge
import json

# ... [Your existing code for connecting and controlling Philips Hue]

# Using modern CSS for styling
css = """
    .block {
        width: 100px !important;
    }

    /* This will ensure the flex items don't grow and occupy the entire space */
    [class^="gradio-container-"] {
        flex-grow: 0 !important;
    }

    /* This will set a width for the blocks */
    .block {
        width: 100px !important;
    }

    /* Increase the size of the colorpicker */
    input[type="color"] {
        width: 100px;
        height: 50px;
        border: none; /* Optionally remove border for aesthetics */
        cursor: pointer; /* Change cursor to a pointer for better UX */
    }

    .gap {
        min-width: 125px !important;
    }

    .stretch {
        flex-grow: 0 !important;
        display: block ruby !important
    }

    #md_name {
        width: 180px !important;
    }

    #md_title {
        width: 800px !important;
    }

"""

def build_gradio():

    lights, groups, grouped_lights = get_lights('192.168.178.29')

    with gr.Blocks(css=css) as app:

        # create a markdown block with the group name
        gr.Markdown(f"""
                    # Davids Hue Controller

                    {len(lights)} lights and {len(groups)} groups found
                    
                    """,
                    elem_id="md_title"
                    
                    )

        # Iterate over each group and its lights
        for group_name, light_names in grouped_lights.items():

            # skip entertainment areas, currently configured for german
            if "Entertainment-Bereich" in group_name:
                continue

            with gr.Row():

                # create a markdown block with the group name
                gr.Markdown(f"## {group_name}", elem_id="md_name")

                for light_name in light_names:

                    with gr.Column():
                        color_picker = gr.ColorPicker(value="#ffffff", label=f"{light_name}")

                        # also update whenever the color of the color_picker is changed
                        color_picker.change(
                            lambda hex_color, ln=light_name: control_lightstrip(lights, ln, hex_color),
                            inputs=[color_picker],
                            outputs=[]
                        )

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inline=False,
        inbrowser=True
    )

if __name__ == "__main__":
    build_gradio()