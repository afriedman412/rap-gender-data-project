# Rap Gender Data Project
We are in a golden age of female rap!!! Rap has historically been dominated by men, as reflected in the charts and the canon. This is not to downplay the contributions of numerous women (and female-identifying people) to the genre, but on numbers alone they are in the minority. In the last decade, however, the trend has swung in the opposite direction. While still far from parity, women are significantly better represented practically everywhere within the genre.

Given the several-fold increase in rap by women, I got an idea for a data project a few months ago: **Could I train a model to correctly guess the gender of a rapper that said a given line?**

For the time being, the answer is **"no" or at least "not yet"**.

I pulled over 200,000 verses from some 600 artists from Genius, then trained a few models to perform sentence classification on that data, to little success. It is entirely possible that this is an impossible task, but there are also plenty of ways I could improve on my work.

In the mean time, however, I have been searching for a job. So I figured I would write up the preliminary work I did to acquire, clean, standardize and optimize the data before I started training models, as a case study in how I approach this kind of work.

# A Notes On The Data:
The focus of this project is the lyrics of this generation of female rappers in context. My approach to assembling the data was to include every female rapper I could find, and then to make sure the data included male counterparts for differentiation. I added rappers in pairs as much as possible: Cardi B and Offset, Nicki Minaj and Drake, Juicy J and Gangsta Boo, Eve and Jadakiss, Dessa and P.O.S. etc.

As I expanded the data to include more female artists, I included more era and region-appropriate artists to provide more context, but still avoided other (often major) artists to avoid overrepresentation. I still had to correct for that!

Anyways, there is nothing about this data that is canonical or "definitive". This is by no means an "official" representation of Rap Lyrics, and nobody should use it like that. Any omissions are 100% accidental or incidental, not reflections of my feelings about certain artists.