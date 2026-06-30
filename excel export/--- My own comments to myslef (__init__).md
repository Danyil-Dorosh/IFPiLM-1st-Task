--- My own comments to myslef (__init__)

- Translate all to English
- zbierz połowania:
    adaptive points fit\sigma clipping.ipynb
    pha_lib\config.py
    pha_lib\model.py

-put eamples in "[]"
-nich farbuje to tez

-if find smth ambigious to realize, ask me

-ad we 

--- Structurized documentation



in @file:excel export.ipynb  write library package in Python to export fit data/graphs of injection/fit to Ecel table (and colour it)
1. Read @file:example.xlsx - thats sheet/sampel for how table
    a) Look (load up) table's comments/notes (Excel cells' fucntionality, not speific column/row)
A)

I. Context for understanding: @file:model.py, @file:sigma clipping.ipynb, @file:discharges.py 

+ III. Table's structure:
    A) Section B2:I5 | Systematic information (configurations)
        1. Sub-Section B3:D5 | Physics constraints/configs
            @file:sigma clipping.ipynb
                #sym:LINE_E        = 6660.0 
                #sym:HALF_W        = 60.0
                #sym:CHANNEL_ID    = 2
        3. Sub-Section E3:F5 | Injection detection constraints/configs
            @file:model.py
                #sym:InjectionDetectionConfig 
                    #sym:min_jump 
                    #sym:threshold_factor 
        3. Sub-Section G3:I5 | Fit constraints/configs
            @file:sigma clipping.ipynb
                #sym:sigma_thresh = 1
                #sym:min_inliers = 4
                #sym:max_iter = 10

    B) Section B8:... | Injections & fits
        1. Column B | Discahrges [Example - B10:B15]
            All the injections of 1 discharge will be gouped under 1 discharge
            Cells of that colum will be "merged", with 1 label, which is date & hour of a Discharge's object
            @file:discharges.py
                #sym:Discharge
                    #sym:discharge_id 
        2. Column C | Injections [Example - C10:C15]
            Each row - separated injection
            @file:model.py
                #sym:Injection
                    #sym:injection_no
        3. Sub-section: Columns D:L | Exponential fit model coeeficients
            #sym:fit_sigma_clip -> 
                 #sym:A_fit, #sym:tau_fit, #sym:t_0 ,#sym:C_bg ,#sym:A_err, #sym:tau_err ,tau_err_relm,#sym:red_chi2 
            n [Column L] is amount of poits take to fit per all of the injection's ("5/7", for instance, mean 5 point taken out of 7 to fit)
        4. Sub-section: Columns M:P | Injection info
            @file:model.py
                a) Column M:N | Graphs of inejction+fit from sigma clipping.ipynb-like. (imges in cell)
                #sym:Injection
                    #sym:start_frame
                    #sym:finish_frame
        5. Meaning of collors (only cells of columns from C to P are coloured - each of 1 injection)
            It bases ob tau error
                <7 - green
                (7;12] - yellow
                (12;25] - orange
                25< - red



II. Package's structure
    A) user input: 
        1. result dictionary of #sym:fit_sigma_clip function (hacky that dedicated object is not created for function result - but that's what we work on now);
        2. #sym:fig and  #sym:ax (but we will mostly use ax);
            !!Package do nothing with it except export it as a picture in cell
        3. #sym:Discharge object, whisch have #sym:Injection Inject objects in it;
        4. Path to output folder ("output\excel_export" for default)
    B) 1 function for export
    C) Fucntion-modularity philosofy - although 1 uer function - it is more of lego-blocks



IIII. Stages & Intructions:
    - DO NOT READ TABLE TO CHECK WHETHER IT WAS DONE PROPERLY. I AM THE ONLY ADMIRING SIDE (after each step implying/etending table, ask me for relust's check-up)
    - we WILL NOT WRITE THT WHOLE IN 1 TIME FOR SURE (just too much code -)
    After each stage - i will check the property
    STAGES
        A) Suggest names for columns, parts, cells
        B) Test "empty data" sheet (to check proper titles format)
        C) load up test folder (use pickel as in @file:sigma clipping.ipynb) & make sigma_clip fit (just copy it to new notebook at some cell) on it export to excel
        D) load up (through pickles) all discharges and sigma-fit them and export to excel
        E) load up (through pickles) 3 discharges and sigma-fit them and export to excel
        F) Inply colouring (just export all discharge with fits again) and export 3 discharges
        G) Inply colouring (just export all discharge with fits again) and export all discharges
    

--- Journaling-ish word-ish explanation
 So the first thing will be the upper left header with systematic information about about just everything how cut works like this small window from B2 to I5 is just a window where I can save information about how generally was fit taken how the injection were detected so like this will be like config information and the systematic information is separated to three parts physics part which is just for like explanation about what we taking as a physics variable for instance that the line like the that we take for instance 6660 electron volts 6660 electron volts as our point that's the first column B the second C1 is what how window do we choose to integrate to calculate the events for this case it's just 60 electron volts the D column is channel ID which is about what channel do we pick from the discharge because there are four channels and we use only the second one so it will be always the second the second part of systematic information is fit config configurations of fitting the first one is sigma threshold as we use sigma clipping it just the value of sigma threshold we use for all the fit mean mean points in liners which means the F column mean points in fighters will mean which mean how point much points do we need for minimum to make our fit it's actually four pretty simple and the sigma threshold is one Uh the max eater is max amount of interaction we do at sigma clipping method. So actually also those three um variables, techno threshold, mean points in liners and max eater, you can find in that file. Uh as well as in this file, you can find physics configuration, 6660 electron volts, 60 electron volts as a half window and that is a second channel ID. The sort part of systematic information injection detection config is configuration of injection detection. The first one is mean jump, which is 20 electron volts. You can also find those configuration in file config.py. And the second one is threshold factor, uh which is you can also find in that file, which just means like how much have they have it to be above the medium to start counting that as a threshold. The second part is very much the information of fits we use. So that is the upper part and after, let's say, in that table after B9, we have after B9 till the very other down right part, we just have the table of of very much injections and discharges. So the B column is uh discharges, which discharge is it and will be just discharge time and each discharge discharge like discharge will reunite several cells. Like we have like we are going at at the rows, like each row is each injection and uh you have the at the B column, like to which discharge few injections go to. So discharge time will be like a separate like merged will be merged cells. So you can actually see the example. I like giving examples in that example table so you would understand. The C column is injection number. In this example, there are six injections, but it may as well be three injections or two injections depending on the variable we will get. The third column and then we have like the part of columns which will correspond for the coefficients of our exponential fit and physical values because as you remember, check file that and that there are physical values and frame values values. Frame values are because we use frames and amounts in our data, but we just then convert it to physical ones using that. So as the column is coefficient A, E column is the error of A, F column is tau coefficient, G column is error of tau, H column is relative error of tau as it's pretty important, especially relative tau is pretty important. Then in I column, we have T0, which remember is not the same as the frame of the beginning and the end of the injection, because the injection may be long, but we can take actually small like piece of that to fit. So T0 is that the first um value we take, the first frame we take for our fit. Then we have see background, which is our just background, uh, which is just background, which is just coefficients, you know what?
And then we have reduced chi squared, which you will also take like check file to understand what each values of those are for.
Then this is the part of, uh, values wired to fitting, because then there is other that part, which is the one row, which is just general information about the, oh no, and I forgot, there is another one column in the fit section, N, which corresponds to how much points of all the injection do we take for our fit.
It is amount of points we taken slash the whole length of the injection.
It is good statistic to just generally know that maybe we have taken only half of all points of injection to fit.
Then we have information about the injection columns, the column N is for injection start frame, column O is for injection finish frame, then, uh, going still of the injection, uh, part, we have a DP column, you will save the image, uh, of the graph plus fit, look at the file to understand how it is done, and in the column Q, uh, and column PQ, the difference that in column P, the image of graph plus fit is in the logarithm scale, whereas natural logarithm scale, whereas in Q column, you have usual scale.
So in these cells, we will save the images of the fit.