import pandas as pd
from typing import Literal
from langchain_core.tools import tool
from models import *
from datetime import datetime


@tool
def check_availability_by_doctor(desired_date:DateModel, doctor_name:Literal['kevin anderson','robert martinez','susan davis','daniel miller','sarah wilson','michael green','lisa brown','jane smith','emily johnson','john doe']):
    """
    Checking the database if we have availability for the specific doctor.
    The parameters should be mentioned by the user in the query
    """
    df = pd.read_csv(r"../data/doctor_availability.csv")
    
    #print(df)
    
    df['date_slot_time'] = df['date_slot'].apply(lambda input: input.split(' ')[-1])
    
    rows = list(df[(df['date_slot'].apply(lambda input: input.split(' ')[0]) == desired_date.date)&(df['doctor_name'] == doctor_name)&(df['is_available'] == True)]['date_slot_time'])

    if len(rows) == 0:
        output = "No availability in the entire day"
    else:
        output = f'This availability for {desired_date.date}\n'
        output += "Available slots: " + ', '.join(rows)

    return output


@tool
def check_availability_by_specialization(desired_date:DateModel, specialization:Literal["general_dentist", "cosmetic_dentist", "prosthodontist", "pediatric_dentist","emergency_dentist","oral_surgeon","orthodontist"]):
    """
    Checking the database if we have availability for the specific specialization.
    The parameters should be mentioned by the user in the query
    """
    #Dummy data
    df = pd.read_csv(r"../data/doctor_availability.csv")
    df['date_slot_time'] = df['date_slot'].apply(lambda input: input.split(' ')[-1])
    rows = df[(df['date_slot'].apply(lambda input: input.split(' ')[0]) == desired_date.date) & (df['specialization'] == specialization) & (df['is_available'] == True)].groupby(['specialization', 'doctor_name'])['date_slot_time'].apply(list).reset_index(name='available_slots')

    if len(rows) == 0:
        output = "No availability in the entire day"
    else:
        def convert_to_am_pm(time_str):
            # Split the time string into hours and minutes
            time_str = str(time_str)
            hours, minutes = map(int, time_str.split("."))
            
            # Determine AM or PM
            period = "AM" if hours < 12 else "PM"
            
            # Convert hours to 12-hour format
            hours = hours % 12 or 12
            
            # Format the output
            return f"{hours}:{minutes:02d} {period}"
        output = f'This availability for {desired_date.date}\n'
        for row in rows.values:
            output += row[1] + ". Available slots: \n" + ', \n'.join([convert_to_am_pm(value)for value in row[2]])+'\n'

    return output


@tool
def set_appointment(desired_date:DateTimeModel, id_number:IdentificationNumberModel, doctor_name:Literal['kevin anderson','robert martinez','susan davis','daniel miller','sarah wilson','michael green','lisa brown','jane smith','emily johnson','john doe']):
    """
    Set appointment or slot with the doctor.
    The parameters MUST be mentioned by the user in the query.
    """
    df = pd.read_csv(r"../data/doctor_availability.csv")
   
    # Debug print to check the input format
    print(f"Received date string: {desired_date.date}")
    
    def convert_datetime_format(dt_str):
        # Remove "at" if present in the string
        if " at " in dt_str:
            dt_str = dt_str.replace(" at ", " ")
            
        try:
            # First try the DD-MM-YYYY HH:MM format
            dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
            # Format to match database format
            return dt.strftime("%d-%m-%Y %H.%M")
        except ValueError:
            try:
                # Try alternative format YYYY-MM-DD HH:MM
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                # Format to match database format
                return dt.strftime("%d-%m-%Y %H.%M")
            except ValueError:
                print(f"Failed to parse date: {dt_str}")
                raise ValueError(f"Date format not recognized. Please use DD-MM-YYYY HH:MM format")
    
    try:
        formatted_date = convert_datetime_format(desired_date.date)
        print(f"Formatted date for DB lookup: {formatted_date}")
        
        # Check if the appointment is available
        case = df[(df['date_slot'] == formatted_date) & 
                (df['doctor_name'] == doctor_name) & 
                (df['is_available'] == True)]
        
        if len(case) == 0:
            return "No available appointments for that particular date and time. Please try another time slot."
        else:
            # Update the dataframe
            df.loc[(df['date_slot'] == formatted_date) & 
                (df['doctor_name'] == doctor_name) & 
                (df['is_available'] == True), 
                ['is_available', 'patient_to_attend']] = [False, id_number.id]
            
            # Save changes
            df.to_csv(r'../data/doctor_availability.csv', index=False)
            
            return f"Appointment successfully booked with Dr. {doctor_name.title()} on {desired_date.date}."
    except Exception as e:
        print(f"Error in set_appointment: {str(e)}")
        return f"There was an issue booking your appointment: {str(e)}"


@tool
def cancel_appointment(date:DateTimeModel, id_number:IdentificationNumberModel, doctor_name:Literal['kevin anderson','robert martinez','susan davis','daniel miller','sarah wilson','michael green','lisa brown','jane smith','emily johnson','john doe']):
    """
    Canceling an appointment.
    The parameters MUST be mentioned by the user in the query.
    """
    df = pd.read_csv(r"../data/doctor_availability.csv")
    
    def convert_datetime_format(dt_str):
        # Remove "at" if present in the string
        if " at " in dt_str:
            dt_str = dt_str.replace(" at ", " ")
            
        try:
            # First try the DD-MM-YYYY HH:MM format
            dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
            # Format to match database format
            return dt.strftime("%d-%m-%Y %H.%M")
        except ValueError:
            try:
                # Try alternative format YYYY-MM-DD HH:MM
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                # Format to match database format
                return dt.strftime("%d-%m-%Y %H.%M")
            except ValueError:
                print(f"Failed to parse date: {dt_str}")
                raise ValueError(f"Date format not recognized. Please use DD-MM-YYYY HH:MM format")
    
    try:
        formatted_date = convert_datetime_format(date.date)
        
        case_to_remove = df[(df['date_slot'] == formatted_date) & 
                          (df['patient_to_attend'] == id_number.id) & 
                          (df['doctor_name'] == doctor_name)]
        
        if len(case_to_remove) == 0:
            return "You don't have any appointment with those specifications"
        else:
            df.loc[(df['date_slot'] == formatted_date) & 
                 (df['patient_to_attend'] == id_number.id) & 
                 (df['doctor_name'] == doctor_name), 
                 ['is_available', 'patient_to_attend']] = [True, None]
            
            df.to_csv(r'../data/doctor_availability.csv', index=False)
            return "Appointment successfully cancelled"
    except Exception as e:
        print(f"Error in cancel_appointment: {str(e)}")
        return f"There was an issue canceling your appointment: {str(e)}"


@tool
def reschedule_appointment(old_date:DateTimeModel, new_date:DateTimeModel, id_number:IdentificationNumberModel, doctor_name:Literal['kevin anderson','robert martinez','susan davis','daniel miller','sarah wilson','michael green','lisa brown','jane smith','emily johnson','john doe']):
    """
    Rescheduling an appointment.
    The parameters MUST be mentioned by the user in the query.
    """
    df = pd.read_csv(r"../data/doctor_availability.csv")
    
    def convert_datetime_format(dt_str):
        # Remove "at" if present in the string
        if " at " in dt_str:
            dt_str = dt_str.replace(" at ", " ")
            
        try:
            # First try the DD-MM-YYYY HH:MM format
            dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
            # Format to match database format
            return dt.strftime("%d-%m-%Y %H.%M")
        except ValueError:
            try:
                # Try alternative format YYYY-MM-DD HH:MM
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                # Format to match database format
                return dt.strftime("%d-%m-%Y %H.%M")
            except ValueError:
                print(f"Failed to parse date: {dt_str}")
                raise ValueError(f"Date format not recognized. Please use DD-MM-YYYY HH:MM format")
    
    try:
        formatted_old_date = convert_datetime_format(old_date.date)
        formatted_new_date = convert_datetime_format(new_date.date)
        
        # Check if the old appointment exists
        old_appointment = df[(df['date_slot'] == formatted_old_date) & 
                           (df['patient_to_attend'] == id_number.id) & 
                           (df['doctor_name'] == doctor_name)]
        
        if len(old_appointment) == 0:
            return "You don't have an existing appointment with those specifications"
        
        # Check if the new slot is available
        available_for_desired_date = df[(df['date_slot'] == formatted_new_date) & 
                                      (df['is_available'] == True) & 
                                      (df['doctor_name'] == doctor_name)]
        
        if len(available_for_desired_date) == 0:
            return "No available slots for the desired new date and time"
        else:
            # Cancel old appointment
            df.loc[(df['date_slot'] == formatted_old_date) & 
                 (df['patient_to_attend'] == id_number.id) & 
                 (df['doctor_name'] == doctor_name), 
                 ['is_available', 'patient_to_attend']] = [True, None]
            
            # Book new appointment
            df.loc[(df['date_slot'] == formatted_new_date) & 
                 (df['doctor_name'] == doctor_name) & 
                 (df['is_available'] == True), 
                 ['is_available', 'patient_to_attend']] = [False, id_number.id]
            
            df.to_csv(r'../data/doctor_availability.csv', index=False)
            return f"Successfully rescheduled appointment with Dr. {doctor_name.title()} from {old_date.date} to {new_date.date}"
    except Exception as e:
        print(f"Error in reschedule_appointment: {str(e)}")
        return f"There was an issue rescheduling your appointment: {str(e)}"