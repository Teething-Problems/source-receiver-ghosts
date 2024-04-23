import base64
import bs4
from bokeh.layouts import column, layout
from bokeh.models import (CustomJS, Slider, Div,
                          PanTool, WheelZoomTool, UndoTool,
                          ResetTool, SaveTool, CustomAction,
                          HoverTool) 
from bokeh.plotting import ColumnDataSource, figure, output_file, save 
import numpy as np

HTML_OUT = "./index.html"

SAMPLE_INTERVAL = 2.0 # ms
SOURCE_DEPTH = 6.0 # m
RECEIVER_DEPTH = 10.0 # m
WATER_VELOCITY = 1500.0 # m/s
INCIDENCE_ANGLE = 0.0 # degrees

# theme
THEME_BACKGROUND = '#141B2D'
THEME_FOREGROUND = '#1F2941'
THEME_HIGHLIGHT1 = '#35E8FB'
THEME_HIGHLIGHT2 = '#7065D6'
THEME_HIGHLIGHT3 = '#E9C4FD'
THEME_ANNOTATION = '#FFFFFF'

theme_css = f"""
<style>
html {{
    background-color: {THEME_BACKGROUND};
    }}
.bk-root .bk-toolbar.bk-right .bk-toolbar-button.bk-active {{
    border-left-color: {THEME_HIGHLIGHT1} !important;
    }}
.bk-root .bk-toolbar-button:hover {{
    background-color: {THEME_FOREGROUND};
    }}
.bk-root .bk-slider-title {{
    color : white;
    }}
</style>
"""

# initial plot data
fmax = (0.5 / SAMPLE_INTERVAL) * 1000
x = np.linspace(0.01, fmax, 1000)
tr = np.radians(INCIDENCE_ANGLE)
tsghost = (2.0 * SOURCE_DEPTH * np.cos(tr)) / WATER_VELOCITY
trghost = (2.0 * RECEIVER_DEPTH * np.cos(tr)) / WATER_VELOCITY
sterm = 0.5 * 2.0 * np.pi * x * tsghost
rterm = 0.5 * 2.0 * np.pi * x * trghost
sghost = np.abs(1.0 / (4.0 * np.sin(sterm)))
rghost = np.abs(1.0 / (4.0 * np.sin(rterm)))
srghost = np.abs(1.0 / (4.0 * np.sin(sterm) * np.sin(rterm)))
y1 = 1.0 - (20.0 * np.log10(sghost))
y2 = 1.0 - (20.0 * np.log10(rghost))
y3 = 1.0 - (20.0 * np.log10(srghost))

# set column data source for plot
source = ColumnDataSource(data=dict(x=x, y1=y1, y2=y2, y3=y3))

# JavaScript for slider interactive callback
slider_callback = CustomJS(args=dict(source=source), code="""
    let data = source.data;
    let sd = sdepth.value;
    let rd = rdepth.value;
    let vw = vwater.value;
    let td = angle.value;
    let x = data['x'];
    for (let i = 0; i < x.length; i++) { 
        tr = td * (Math.PI/180);
        tsghost = (2.0 * sd * Math.cos(tr)) / vw;
        trghost = (2.0 * rd * Math.cos(tr)) / vw;
        sterm = 0.5 * 2.0 * Math.PI * x[i] * tsghost;
        rterm = 0.5 * 2.0 * Math.PI * x[i] * trghost;
        sghost = Math.abs(1.0 / (4.0 * Math.sin(sterm)));
        rghost = Math.abs(1.0 / (4.0 * Math.sin(rterm)));
        srghost = Math.abs(1.0 / (4.0 * Math.sin(sterm) * Math.sin(rterm)));
        data.y1[i] = 1.0 - (20.0 * Math.log10(sghost));
        data.y2[i] = 1.0 - (20.0 * Math.log10(rghost));
        data.y3[i] = 1.0 - (20.0 * Math.log10(srghost));
    }
    source.change.emit();
""")

# create the plot
TOOLTIPS = [("frequency, amplitude", "$x, $y")]

WINDOW_OPEN = "window.open('https://github.com/Teething-Problems/source-receiver-ghosts', '_blank');"

code_tool = CustomAction(action_tooltip="See the Python code on GitHub",
                         icon='./github-mark-white.png',
                         callback=CustomJS(code=WINDOW_OPEN)) 

TOOLS = [PanTool(), WheelZoomTool(), UndoTool(),
         ResetTool(), SaveTool(), HoverTool(),
         code_tool]

plot = figure(y_range=(-90, 30), x_range=(0, 250),
              tooltips=TOOLTIPS, tools=TOOLS,
              sizing_mode='stretch_both',
              title="Source & Receiver Ghost Amplitude Spectra")
plot.line('x', 'y1', source=source, line_width=3,
          line_color=THEME_HIGHLIGHT1, legend="source ghost")
plot.line('x', 'y2', source=source, line_width=3,
          line_color=THEME_HIGHLIGHT2, legend="receiver ghost")
plot.line('x', 'y3', source=source, line_width=3,
          line_color=THEME_HIGHLIGHT3, legend="source & receiver ghosts")

# customise the plot
plot.x_range.bounds = 'auto'
plot.toolbar.logo = None
plot.toolbar.active_inspect = None
plot.legend.location = 'bottom_left'
plot.legend.click_policy='hide'
plot.xaxis.axis_label = "frequency (Hz)"
plot.yaxis.axis_label = "amplitude (dB)"
plot.title.text_color = THEME_ANNOTATION
plot.xaxis.axis_label_text_color = THEME_ANNOTATION
plot.yaxis.axis_label_text_color = THEME_ANNOTATION
plot.xaxis.major_tick_line_color = THEME_ANNOTATION
plot.yaxis.major_tick_line_color = THEME_ANNOTATION
plot.xaxis.minor_tick_line_color = THEME_ANNOTATION
plot.yaxis.minor_tick_line_color = THEME_ANNOTATION
plot.xaxis.major_label_text_color = THEME_ANNOTATION
plot.yaxis.major_label_text_color = THEME_ANNOTATION
plot.xaxis.axis_line_color = THEME_ANNOTATION
plot.yaxis.axis_line_color = THEME_ANNOTATION
plot.legend.background_fill_color = THEME_BACKGROUND
plot.legend.label_text_color = THEME_ANNOTATION
plot.background_fill_color = THEME_FOREGROUND
plot.border_fill_color = THEME_BACKGROUND

# sliders
sdepth_slider = Slider(start=1.0, end=20.0, value=SOURCE_DEPTH,
                       step=0.5, title="source depth (m)",
                       callback=slider_callback)
slider_callback.args['sdepth'] = sdepth_slider
rdepth_slider = Slider(start=1.0, end=20.0, value=RECEIVER_DEPTH,
                       step=0.5, title="receiver depth (m)",
                       callback=slider_callback)
slider_callback.args['rdepth'] = rdepth_slider
vwater_slider = Slider(start=1450.0, end=1550.0, value=WATER_VELOCITY,
                       step=1.0, title="water velocity (m/s)",
                       callback=slider_callback)
slider_callback.args['vwater'] = vwater_slider
angle_slider = Slider(start=0.0, end=90.0, value=INCIDENCE_ANGLE,
                       step=1.0, title="incidence angle (degrees)",
                       callback=slider_callback)
slider_callback.args['angle'] = angle_slider

# layout, including plot and sliders
style = Div(text=theme_css)
sliders = column([sdepth_slider, rdepth_slider,
                  vwater_slider, angle_slider],
                 sizing_mode='stretch_width')
col = column([style, plot, sliders])

# output layout to html
output_file(HTML_OUT, title="Source & Receiver Ghosts")
save(layout([col], sizing_mode='stretch_both'))

# update the html file
tabicon = base64.b64encode(open("./github-mark.png", "rb").read()).decode('ascii')
tabicon = 'data:image/png;base64,' + tabicon

with open(HTML_OUT) as f:
    soup = bs4.BeautifulSoup(f.read())  
    
new_tag = soup.new_tag('link', rel='icon', type='image/png',
                       href=tabicon)
soup.head.append(new_tag)

with open(HTML_OUT, "w") as f:
    f.write(str(soup))