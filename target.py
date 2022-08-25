#!/usr/bin/python

# reference material
# /usr/share/inkscape/extensions
# /usr/share/inkscape/extensions/inkex.py
# 

import math, inkex, simplepath, sys, simplestyle
from lxml import etree

class Target(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--distance",type=int,default=100,dest="distance",
                          help="distance from target")
        pars.add_argument("--tab",type=ascii,default=100,dest="tab",
                          help="The selected UI-tab when OK was pressed")

    def effect(self):
        self.group = self.svg.get_current_layer().add(inkex.Group.new('target'))
        circles = Circles(self)
        if len(circles.circles) <= 2:
            inkex.errormsg('select more than 2 circles')
            return None
        apc = circles.average_precision_circle()
        circles.draw_circle(apc)
        circles.draw_plus((apc[0],apc[1]))
        apc_in = circles.average_precision_circle_inches(apc)
        moa = circles.moa(apc_in[2]*2,distance=self.options.distance)
        hv_avg_precision = circles.average_horizontal_vertical_precision( \
            distance=self.options.distance)
        es = circles.extreme_spread(distance=self.options.distance)
     
        output = "%d shots, %d yards to target\n" % \
            (len(circles.circles),self.options.distance) + \
            "mean precision = %.2f in, %.2f moa\n" % \
            (apc_in[2]*2,moa) + \
            "mean horiz precision   = %.2f in, %.2f moa\n" % \
            (hv_avg_precision[0],hv_avg_precision[1]) + \
            "mean vert precision    = %.2f in, %.2f moa\n" % \
            (hv_avg_precision[2],hv_avg_precision[3]) + \
            "extreme spread    = %.2f in, %.2f moa" % \
            (es[0],es[1])

        size = self.svg.unittouu('%.2f in' % apc_in[2])
        size = size + (self.svg.unittouu('10 px')*2)

        circles.draw_text(output,(apc[0]+0,apc[1]+size))

class Circles:
    '''circles grabs all selected circles, finds various stats
       and writes statistical info to the svg document'''
    def __init__(self,effect):
        self.effect = effect
        self.circles = []
        self.get_circles_from_effect()
        self.name = 'target-average-precision'
        self.center = self.average_center()        

    def parent(self):
        '''this grabs the parent of one of the circles...so I can use
           it to draw more'''
        return self.circles[0].node.getparent()

    def draw_circle(self,sometuple):
        '''draw a circle on the same svg parent as the rest of the circles
          input is a tuple of (x,y,r)
          output is svg on parent'''
        x = sometuple[0]
        y = sometuple[1]
        r = sometuple[2]
        sw = self.effect.svg.unittouu('1 px')
        circ_style = { 'stroke':str('#ff0000'),
                       'fill': 'none',
                       'stroke-width':str(sw)  }
        circ_attribs = {'cx':str(x), 'cy':str(y), 'r':str(r)}
        e = self.effect.group.add(inkex.Circle(**circ_attribs))
        e.style = circ_style
        e.label = 'circle'

    def draw_plus(self,point,size=20):
        '''draw a red target plus at the given point tuple (x,y)'''
        fs = self.effect.svg.unittouu(str(size)+' px')
        self.draw_line((point[0]-fs/2,point[1]),(point[0]+fs/2,point[1]))
        self.draw_line((point[0],point[1]-fs/2),(point[0],point[1]+fs/2))

    def draw_line(self,point1,point2):
        '''draw a 1px red line from point1 to point2
           on the same parent element as one of the circles
           input points are tuples of (x,y)'''

        sw = self.effect.svg.unittouu('1 px')

        line_style = { 'stroke':str('#ff0000'),
                       'stroke-width':str(sw)  }
        #line_attribs = { 'M '+str(point1[0])+
        #    ','+str(point1[1])+' L '+str(point2[0])+','+str(point2[1])}

        line_attribs = { 'x1':str(point1[0]),'y1':str(point1[1]),
                         'x2':str(point2[0]),'y2':str(point2[1]) }

        e = self.effect.group.add(inkex.Line(**line_attribs)) 
        e.style = line_style
        e.label = 'line'

    def draw_text(self,text,point):
        '''draws red 10 pt text starting at the given point tuple(x,y)'''
        x = point[0]
        y = point[1]
        font_size = 10

        fs = self.effect.svg.unittouu(str(font_size)+' px')

        text_style = { 'font-family':str('DejaVu Sans'),
                       'font-style':str('normal'),
                       'font-variant':str('normal'),
                       'font-weight':str('normal'),
                       'font-stretch':str('normal'),
                       'font-size':str(fs),
                       'fill':str('#ff0000'),
                       'fill-opacity':str('1'),
                       'stroke':str('none') }
        text_attribs = { 'x':str(x), 'y':str(y) }
        t = self.effect.group.add(inkex.TextElement(**text_attribs))
        t.style = text_style
        t.label = 'text'

        text = str(text).split("\n")
        for s in text:
            text_attribs = { 'x':str(x), 'y':str(y) }
            span = t.add(inkex.Tspan(**text_attribs))
            span.text = str(s)
            y += fs

    def get_circles_from_effect(self):
        '''this gets all circles from the effect and
           stores them in a class array'''
        for node in self.effect.svg.selected.values():
            if not self.is_circle(node):
                continue
            try:
                circle = Circle(node)
                self.circles.append(circle)
            except:
                continue
 
    def is_circle(self,node):
        if node.tag == "{http://www.w3.org/2000/svg}circle":
            return True
        return False

    def min_x(self):
        '''iterate over all circles return the circle with the
           lowest X coordinate'''
        minx = self.circles[0].x
        minx_circle = None
        for circle in self.circles:
            if circle.x <= minx:
                minx = circle.x
                minx_circle = circle
        return minx_circle
         
    def min_y(self):
        '''iterate over all circles return the circle with the
           lowest Y coordinate'''
        miny = self.circles[0].y
        miny_circle = None
        for circle in self.circles:
            if circle.y <= miny:
                miny = circle.y
                miny_circle = circle
        return miny_circle

    def extreme_spread(self,distance=100):
       '''the furthest distance between two holes in a target
          center to center. returns tuple of (inches,moa)'''
       max = 0
       for circle1 in self.circles:
           for circle2 in self.circles:
               x = abs(circle1.x-circle2.x)
               y = abs(circle1.y-circle2.y)
               d = math.sqrt(x*x + y*y)
               if d > max:
                   max = d
       max = self.effect.svg.uutounit(max,'in')
       return (max,self.moa(max,distance))


    def average_horizontal_vertical_precision(self,distance=100):
        '''get separate average components for horizontal
           and vertical. Sometimes it's helpful to know.  Maybe wind
           causes big horizontal spread.  Maybe powder differences
           cause vertical spread.
           returns a tuple of (horizontal inches, horizontal moa,vertical inches,vertical moa)
        '''
        totx = 0
        toty = 0
        for circle in self.circles:
            totx = totx + float(abs(self.center[0]-circle.x))
            toty = toty + float(abs(self.center[1]-circle.y))
        avgx = (totx / len(self.circles))*2
        avgy = (toty / len(self.circles))*2
        avgx = self.effect.svg.uutounit(avgx,'in')
        avgy = self.effect.svg.uutounit(avgy,'in')
        return (avgx,self.moa(avgx,distance),avgy,self.moa(avgy,distance))


    def average_center(self):
        '''calculate the average x and average y from x and y of
           each circle.  returns an (x,y) tuple'''
        minx = self.min_x()
        total = 0
        for circle in self.circles:
            total = total + (circle.x - minx.x)
        x_avg = total/len(self.circles) + minx.x

        miny = self.min_y()
        total = 0
        for circle in self.circles:
            total = total + (circle.y - miny.y)
        y_avg = total/len(self.circles) + miny.y
        return (x_avg,y_avg)

    def average_radius(self):
        '''calculate the average radius (precision) of the group
           of circles. returns a float.'''
        total = 0
        for circle in self.circles:
            x = abs(self.center[0]-circle.x)
            y = abs(self.center[1]-circle.y)
            radius = math.sqrt(x*x + y*y)
            total = total + radius
        return total / len(self.circles)

    def average_precision_circle(self):
        '''returns a tuple of (x,y,radius) that defines the
           average precision of all circles'''
        avgr = self.average_radius()
        return (self.center[0],self.center[1],avgr)

    def average_precision_circle_inches(self,sometuple):
        '''input is a tuple of (x,y,r), output is the same in inches'''
        x = sometuple[0]
        x = self.effect.svg.uutounit(x,'in')
        y = sometuple[1]
        y = self.effect.svg.uutounit(y,'in')
        r = sometuple[2]
        r = self.effect.svg.uutounit(r,'in')
        return (x,y,r)

    def moa(self,span,distance=100):
        '''gives the moa for a given span at a specific distance in yards'''
        moa = float(span)/(1.047*(float(distance)/100))
        return moa

    def __str__(self):
        bigstr = ""
        for circle in self.circles:
            bigstr = bigstr + "%s\n" % circle 
        return bigstr


class Circle:
    def __init__(self,node):
        self.node = node
        self.id = self.node.get('id')
        self.x = float(self.node.get('cx'))
        self.y = float(self.node.get('cy'))
        self.r = float(self.node.get('r'))

    def __str__(self):
        return "%s x=%s y=%s r=%s" % (self.id,self.x,self.y,self.r)

if __name__ == '__main__':
    e = Target()
    e.run()
