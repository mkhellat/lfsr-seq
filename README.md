# lfsr-seq

Tool to play around with LFSR sequences

# Run

This should be run on a system having SageMath 9.7 and with python3. -
https://www.sagemath.org/

````
./lfsr-seq <coeffs_csv_filename> <GF_order>
````

CSV file is used so you could feed multiple series of LFSR
coefficients to the toy and of course the order of the Finite Field
should be given so that multiplication and addition operations are
done modulo the order.

For the sample csv file in the repo, you could run

````
./lfsr-seq strange.csv 2
````


# GNU GPL v3+

Copyright (C) 2023 Mohammadreza Khellat GNU GPL v3+

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
USA.

See also https://www.gnu.org/licenses/gpl.html
