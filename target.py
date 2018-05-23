#!/usr/bin/python

# reference material
# /usr/share/inkscape/extensions
# /usr/share/inkscape/extensions/inkex.py
# 

import math, inkex, simplepath, sys, simplestyle

class Target(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--distance",
            action="store", type="int", 
            dest="distance", default=100,
            help="distance from target")

        self.OptionParser.add_option("--tab",
            action="store", type="string",
            dest="tab",
            help="The selected UI-tab when OK was pressed")

    def effect(self):
        circles = Circles(self)
        if len(circles.circles) <= 2:
            inkex.errormsg('select more than 2 circles')
            return None
        #print circles
        apc = circles.average_precision_circle()
        circles.draw_circle(apc)
        circles.draw_plus((apc[0],apc[1]))
        apc_in = circles.average_precision_circle_inches(apc)
        moa = circles.moa(apc_in,distance=self.options.distance)

        circles.draw_text('%s shots\naverage precision = %.2f inches\nmoa at %d yds = %.2f' % (len(circles.circles),apc_in[2]*2,self.options.distance,moa),(apc[0]+2,apc[1]+10))


class Circles:
    def __init__(self,effect):
        self.effect = effect
        self.circles = []
        self.get_circles_from_effect()
        self.name = 'target-average-precision'

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
        circ_style = { 'stroke':str('#ff0000'),
                       'fill': 'none',
                       'stroke-width':str('1')  }
        circ_attribs = {'style':simplestyle.formatStyle(circ_style),
            inkex.addNS('label','inkscape'):self.name,
            'cx':str(x), 'cy':str(y), 'r':str(r)}
        inkex.etree.SubElement(self.parent(), 
            inkex.addNS('circle','svg'), circ_attribs )

    def draw_plus(self,point,size=20):
        '''draw a red target plus at the given point tuple (x,y)'''
        self.draw_line((point[0]-size/2,point[1]),(point[0]+size/2,point[1]))
        self.draw_line((point[0],point[1]-size/2),(point[0],point[1]+size/2))

    def draw_line(self,point1,point2):
        '''draw a 1px red line from point1 to point2
           on the same parent element as one of the circles
           input points are tuples of (x,y)'''
        line_style = { 'stroke':str('#ff0000'),
                       'stroke-width':str('1')  }
        line_attribs = {'style':simplestyle.formatStyle(line_style),
            inkex.addNS('label','inkscape'):self.name, 'd':'M '+str(point1[0])+
            ','+str(point1[1])+' L '+str(point2[0])+','+str(point2[1])}
        inkex.etree.SubElement(self.parent(), 
            inkex.addNS('path','svg'), line_attribs )

    def draw_text(self,text,point):
        '''draws red 10 pt text starting at the given point tuple(x,y)'''
        x = point[0]
        y = point[1]
        font_size = 10
        text_style = { 'font-family':str('DejaVu Sans'),
                       'font-style':str('normal'),
                       'font-variant':str('normal'),
                       'font-weight':str('normal'),
                       'font-stretch':str('normal'),
                       'font-size':str(font_size),
                       'fill':str('#ff0000'),
                       'fill-opacity':str('1'),
                       'stroke':str('none') }
        text_attribs = { 'style':simplestyle.formatStyle(text_style),
                         'x':str(x),
                         'y':str(y),
                         inkex.addNS('label','inkscape'):self.name }
        t = inkex.etree.SubElement(self.parent(), 
            inkex.addNS('text','svg'), text_attribs )
        text = str(text).split("\n")
        for s in text:
            span = inkex.etree.SubElement( t, inkex.addNS('tspan','svg'),
                { 'x':str(x),
                  'y':str(y),
                  inkex.addNS("role","sodipodi"):"line",})
            y += font_size
            span.text = str(s)
             

    def get_circles_from_effect(self):
        '''this gets all circles from the effect and
           stores them in a class array'''
        #for id, shit in self.effect.doc_ids.iteritems():
        for id, node in self.effect.selected.iteritems():
            #node = self.effect.getElementById(id)
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

    def average_center(self):
        '''get the average x and average y from minx and min y of
           each circle.  returns an (x,y) tuple'''
        minx = self.min_x()
        total = 0
        for circle in self.circles:
            total = total + (circle.x - minx.x)
        x_avg = total/(len(self.circles)-1) + minx.x

        miny = self.min_y()
        total = 0
        for circle in self.circles:
            total = total + (circle.y - miny.y)
        y_avg = total/(len(self.circles)-1) + miny.y
        return (x_avg,y_avg)

    def average_radius(self):
        '''calculate the average radius (precision) of the group
           of circles. returns a float.'''
        center = self.average_center()
        total = 0
        for circle in self.circles:
            x = abs(center[0]-circle.x)
            y = abs(center[1]-circle.y)
            radius = math.sqrt(x*x + y*y)
            total = total + radius
        return total / len(self.circles)

    def average_precision_circle(self):
        '''returns a tuple of (x,y,radius) that defines the
           average precision of all circles'''
        avgxy = self.average_center()
        avgr = self.average_radius()
        return (avgxy[0],avgxy[1],avgr)

    def average_precision_circle_inches(self,sometuple):
        '''input is a tuple of (x,y,r), output is the same in inches'''
        x = sometuple[0]
        x = self.effect.uutounit(x,'in')
        y = sometuple[1]
        y = self.effect.uutounit(y,'in')
        r = sometuple[2]
        r = self.effect.uutounit(r,'in')
        return (x,y,r)

    def moa(self,sometuple,distance=100):
        '''gives the moa for a given tuple at a specific distance in yards'''
        r = sometuple[2]
        moa = float(r)*2/(1.047*(float(distance)/100))
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
    e.affect()
