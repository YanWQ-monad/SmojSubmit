# SmojSubmit
A sublime plugin to submit code to [SMOJ](http://smoj.nhedu.net).
  
### Installation
1. Open `Command Palette` using menu item `Tools → Command Palette...`
2. Choose `Package Control: Add Repository`
3. Type in `https://github.com/YanWQ-monad/SmojSubmit` and hit `Enter`
4. Open `Command Palette`
5. Choose `Package Control: Install Package`
6. Find `SmojSubmit` and hit `Enter`
7. Restart Sublime Text

### Activation
Activate SmojSubmit by modifying your user preferences file, which you can find using the menu item `Preferences → Package Settings → SMOJ Submit → Setting - User`.
And then you can type in your username and password to the preferences file.

### Usage
First, you must add a comment such as `//1234.cpp`, to tell the script the problem which you want to submit.  
`Right click` your mouse in your cpp file.  
Choose `Submit to SMOJ`, then, it will submit the file to SMOJ.  
Wait for a moment, it will open a new tab to show your result.

### Feature
If you use `freopen` in your code such like these:
``` C++
//freopen("Temp.in" , "r", stdin );
//freopen("Temp.out", "w", stdout);
```
``` C++
/*freopen("1234.in" , "r", stdin );
freopen("1234.out", "w", stdout);*/
```
Do not worry. It will cancel the comment and change it to current problem number when it submit.  
But if you forget to use `freopen`, it will do nothing.

### Q&A
Q: Why I can not click on `Submit to SMOJ`?  
A: You need to make sure you are editing in a cpp file and your username and password is right.

Q: Why it does not create a new tab to show the result?  
A: Because you are submitted an OI-MODE problem.

### Issues
Report it [HERE](https://github.com/YanWQ-monad/SmojSubmit/issues).