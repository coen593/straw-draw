class Email:

    def drawCreate(self, name, draw, code, urlshare, urlmanage):
        body = "<html> <body> <h3>Hi " + name + ", <br>you've created the following draw: " + draw + "!</h3> <br> <p>Provide others with the following link to participate:</p><br>" + urlshare + "<br><p>Click here to manage your draw and trigger it:</p><br>" + urlmanage + "</body> </html>"
        return body

    def participate(self, name, draw, code, urlmanage):
        body = "<html> <body> <h3>Hi " + name + ", <br>you're participating in the following draw: " + draw + "!</h3> <br> <p>Click here to have a look at the draw in which you participate:</p>" + urlmanage + "</body> </html>"
        return body
    
    def drawnMulti(self, name, draw, losers):
        body = "<html> <body> <h3>Hi " + name + ", <br>Unfortunately, you drew the shortest straw in draw " + draw + " and were selected along with " + losers + "!"
        return body

    def drawnOne(self, name, draw, losers):
        body = "<html> <body> <h3>Hi " + name + ", <br>Unfortunately, you drew the shortest straw in draw " + draw + " and were selected!"
        return body
    
    def notDrawnMulti(self, name, draw, losers):
        body = "<html> <body> <h3>Hi " + name + ", <br>Lucky for you - you didn't draw the shortest straw in draw " + draw + " and weren't selected! " + losers + " were selected instead."
        return body
    
    def notDrawnOne(self, name, draw, losers):
        body = "<html> <body> <h3>Hi " + name + ", <br>Lucky for you - you didn't draw the shortest straw in draw " + draw + " and weren't selected! " + losers + " was selected instead."
        return body