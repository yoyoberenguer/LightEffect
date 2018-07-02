

# LightEffect

This program creates 2D light effects onto a pygame surface/image (32 bit PNG file encoded with
alpha channels transparency) and generate shadow.
The files radial4.png, RadialTrapezoid, RadialWarning are controlling the shape and light intensity
of the illuminated area (radial masks).

The class can be easily implemented into a 2D game (top down or horizontal/vertical scrolling) to enhanced
the lighting ambiance.

![alt text](https://github.com/yoyoberenguer/LightEffect/blob/master/ScreenDump.png)

Version 2 changes :

 - Added volumetric effect (animated smoke or plasma) in the illuminated area to set a specific ambiance.
        This effect can also be used for generating force field around a set point.

 - Added warning light (rotational lighting)

 - Implemented shadow projection effects from a light source coordinates (See file Shadows.py for more details and
        credit to Marcus Møller for its shadow algorithms (https://github.com/marcusmoller).

 - Code cleanup and split the code into different modules
    Constant.py
    LoadTextureFile.py
    Shadow.py
    LightDemo.py
    
# Scenes 

![alt text](https://github.com/yoyoberenguer/LightEffect/blob/master/Assets/1.png)  ![alt text](https://github.com/yoyoberenguer/LightEffect/blob/master/Assets/11.png)

![alt text](https://github.com/yoyoberenguer/LightEffect/blob/master/Assets/2.png)  ![alt text](https://github.com/yoyoberenguer/LightEffect/blob/master/Assets/22.png)

    
DEMO available in the directory dist.

*** The assets directory must be in the same location than the executable file 

Have a nice journey

This code comes with a MIT license.

Copyright (c) 2018 Yoann Berenguer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

Please acknowledge and give reference if using the source code for your project.

--------------------------------------------------------------------------------------------------------------------

