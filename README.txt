Phone Registrations Verification Tool
Created by D. Lamb

This tool is used to collect all phone objects from Cisco Call Manager and then collect the
following information for each phone using a combination of AXL and RIS (Real-time Information
Service) API look ups.  The tool will compile this information in to an easy to use CSV file.

The tool will allow you to run two passes to collect the data.  A first pass which captures the
current state of the registrations and a Verification pass, where the data is captured to the
a new CSV and then the two files are compared and a third Diff File is created showing the
differences between the two.

This is useful for miagrations and systemic changes to validate that either a change did or did
not effect the intended phones.  It helps to answer, did a phone get the new firmware, which 
phones did not re-register after a cluster reboot.  ETC.

Data collected:

Device Name
Description
Device Pool
Status
Last Registration state change timestamp
Directory Number
Phone's IP Address
Active Firmware Version
Firmware Download Status
Firmware Download Fail Reason
Phone Type