if the_choice == "exception.png":
    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"exception.png",1,1,1)
                                    
elif the_choice == "indentationerror.png":
        bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"indentationerror.png",1.5,3,0.8)

elif the_choice == "x":
    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"indexerror.png",1,1,1,y_speed = 1.2)
elif the_choice == "m":
    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"memoryerror.png",3,10,0.4,y_speed = 0.2)
elif the_choice == "p":
    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"importerror.png",3,15,0.25,y_speed = 0.2)

elif the_choice == "b":
    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"brokenpipe.png",3,1,0.4,y_speed = 0.5)

elif the_choice == "t":
    bug = Bug(startx + rowindex * spacer,starty - colindex,24,24,"typeerror.png",random.randint(1,7),random.randint(1,7),0.4,y_speed = random.uniform(0.5,1.5))