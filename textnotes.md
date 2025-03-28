# ModernMind Development Approach
This is a document detailing my plans for approaching the programming of ModernMind, a.k.a the CircuitPython code responsible for running the Matrix Portal code for my TV Head project.

## Dev Approach
### Microphone Missing!
- For now, I'll just find some way to autocycle the mouth every second or so. That way, 
I can sort of emulate there ACTUALLY being a microphone attached.
### Remote Control
- Thankfully, it seems like the Adafruit IO library actually COMES with a dashboard I can use online through a web browser. This is PERFECT!
- It WOULD be cool making my own app to control it, buuut that might be for later. That is, if Adafruit IO even has an API for me to use...
- **It does!** That's for later, though. For now, I'll just use the AdafruitIO dashboard for inputs.

## Planned Features

First and foremost, let's consider what features I'm going to have in the prototype spec of this thing. Each feature will have a segment dedicated to it.
- Mixing of mouth movements AND expressions.
- The ability to switch between different face and mouth sets.
- Changable expression sets.
- 'Static' faces and canned animations.  Some remote control will follow these two.
- Smash-related animations. (Locked in/stage bans/etc)

## Reactive Changes
- For all of the below (minus the first), I can likely just add some logic checks within the main loop that constantly check for input from AdafruitIO.
- Here's what I'm thinking: Each of these reactive checks can live inside one conditional statement: was anything sent from AdafruitIO? This will hopefully reduce the amount of checks made per loop.
- If this check passes, then all the other checks are actually run! From there, the rest of the code should operate.

## UPDATE: Connectivity
* Here's how I understand how connectivity works:
    * If ANYTHING changes at all, the 'on_message' function of the client gets set off, 

### Mouth and Expression Mixing
- Honestly, for this one I think I can just apply the transparency color to the expressions. That's all there is to it!

### Face/Mouth Sets
- I've observed that the Display() has things in layers. This is going to be great for the static images, but miiiight suck for adaptive things like faces and mouthes.
* Two options:
    *  Remove all layers above, replace the respective face/mouth, and re-add all the previous layers. I could probably do this with some sort of queue.
    * Find some method or other way to just replace the affected layer.
- I also have to consider if eyes/mouthes should be sync'd or not. Given that it SHOULD tie in with the expressions, probably not.

### Swappable + Additional Tilt Expressions
- So this is more of a pipe dream than anything, but I don't really think four tilt expressions (hereby referred to as 'Tilts') is enough to get the full breadth of emotions I want. Maybe it is, but on the offchance that it ISN'T...
* Like before, there are two approaches:
    * Make tilts fully decoupled. As in, any tilt can be swapped out, irrespective of what layer it's on. This would be a LOT more work. Complicated, but VERY flexible and expressive!
    * Bake in tilts in sets of four. This is TREMENDOUSLY easier, but requires some design thought on how I want to bundle tilts together. Easier, but less flexible!

### Static Images
- These are plenty easy! I already figured out how to make new layers on top of everything else.
- I can probably just make a dictionary with numbers(?) and their respective images.
* Something like...
    * `faceDict = [1:expJimbo,2:expP3]` and so on.

### Animations
- These are uh... gonna be rough. To be honest, I need some new tech that I'm not aware of in order to make these work.
- Because, to be real, setting and unsetting several layers in a row sounds psychotic.
* So, turns out there are (yet again) TWO ways of doing this!
    * Use a spritesheet to MANUALLY make these gifs! I kinda like this approach for looking better on a CRT, buuut this is limited by the fact I suuuuck at drawing. Aw.
    * Use this GIF player program I found that MAY or MAY NOT be compatible with my project. This one is up in the air, as the text thing didn't go so well.


## Work Timeline
* Incorporate Adafruit IO into this project.
    * First, make a test 'input recieved/not recieved' signal.
    * From there, you can experiment with making custom test faces and stuff.
* Jot down the actual plans for additional toggles/expressions/static images
* Find out ways to do animations. Incorporate this into the project.
    * Make some sort of test animation depending on how I'll do this.
* Create a test for swapping eye/mouth types.
    * Once this is done, make several and create the logic to change between em all.
