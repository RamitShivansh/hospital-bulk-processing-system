import requests
import logging
import time
from typing import Optional

class HospitalApiClient:
    """Client for interacting with the Hospital Directory API.
    """

    def __init__(self, base_url: str, session: Optional[requests.Session] = None, logger: Optional[logging.Logger] = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)
    
    def create_hospital(self, hospital_data, batch_id):
        """
        Create a new hospital with the given data and batch ID
        
        Args:
            hospital_data (dict): Hospital data containing name, address, and optional phone
            batch_id (str): UUID for batch processing
        
        Returns:
            dict: The created hospital data
        
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/hospitals/"
        start_time = time.time()
        hospital_name = hospital_data.get('name', 'Unknown')
        
        self.logger.info(f"Creating hospital '{hospital_name}' in batch {batch_id}")
        
        payload = {
            'name': hospital_data['name'],
            'address': hospital_data['address'],
            'creation_batch_id': batch_id,
            'active': False  
        }
        
        if hospital_data.get('phone'):
            payload['phone'] = hospital_data['phone']
            self.logger.debug(f"Hospital '{hospital_name}' includes phone number")
        
        try:
            self.logger.debug(f"Sending POST request to {url}")
            response = self.session.post(url, json=payload)
            elapsed_time = time.time() - start_time
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', response.text)
                except:
                    error_msg = response.text
                
                self.logger.error(f"Failed to create hospital '{hospital_name}': {error_msg} (Status: {response.status_code})")
                raise Exception(f"Failed to create hospital: {error_msg} (Status: {response.status_code})")
            
            response_data = response.json()
            hospital_id = response_data.get('id', 'Unknown')
            self.logger.info(f"Created hospital '{hospital_name}' with ID {hospital_id} in batch {batch_id} ({elapsed_time:.2f}s)")
            return response_data
            
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Network error creating hospital '{hospital_name}': {str(e)} ({elapsed_time:.2f}s)")
            raise Exception(f"Network error creating hospital: {str(e)}")
    
    def activate_batch(self, batch_id):
        """
        Activate all hospitals in the given batch
        
        Args:
            batch_id (str): UUID of the batch to activate
        
        Returns:
            dict: The activation response
        
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/hospitals/batch/{batch_id}/activate"
        start_time = time.time()
        
        self.logger.info(f"Activating hospitals in batch {batch_id}")
        
        try:
            self.logger.debug(f"Sending PATCH request to {url}")
            response = self.session.patch(url)
            elapsed_time = time.time() - start_time
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', response.text)
                except:
                    error_msg = response.text
                
                if response.status_code == 404:
                    self.logger.error(f"Batch {batch_id} not found when attempting to activate ({elapsed_time:.2f}s)")
                    raise Exception(f"Batch {batch_id} not found")
                else:
                    self.logger.error(f"Failed to activate batch {batch_id}: {error_msg} (Status: {response.status_code}, {elapsed_time:.2f}s)")
                    raise Exception(f"Failed to activate batch: {error_msg} (Status: {response.status_code})")
            
            response_data = response.json()
            activated_count = response_data.get('activated_count', 0)
            self.logger.info(f"Activated {activated_count} hospitals in batch {batch_id} ({elapsed_time:.2f}s)")
            return response_data
            
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Network error activating batch {batch_id}: {str(e)} ({elapsed_time:.2f}s)")
            raise Exception(f"Network error activating batch: {str(e)}")
    
    def get_hospitals_by_batch(self, batch_id):
        """
        Get all hospitals in the given batch
        
        Args:
            batch_id (str): UUID of the batch to retrieve
        
        Returns:
            list: List of hospitals in the batch
        
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/hospitals/batch/{batch_id}"
        start_time = time.time()
        
        self.logger.info(f"Retrieving hospitals for batch {batch_id}")
        
        try:
            self.logger.debug(f"Sending GET request to {url}")
            response = self.session.get(url)
            elapsed_time = time.time() - start_time
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', response.text)
                except:
                    error_msg = response.text
                    
                if response.status_code == 404:
                    self.logger.error(f"Batch {batch_id} not found when retrieving hospitals ({elapsed_time:.2f}s)")
                    raise Exception(f"Batch {batch_id} not found")
                else:
                    self.logger.error(f"Failed to get hospitals in batch {batch_id}: {error_msg} (Status: {response.status_code}, {elapsed_time:.2f}s)")
                    raise Exception(f"Failed to get hospitals in batch: {error_msg} (Status: {response.status_code})")
            
            response_data = response.json()
            hospital_count = len(response_data)
            self.logger.info(f"Retrieved {hospital_count} hospitals for batch {batch_id} ({elapsed_time:.2f}s)")
            return response_data
            
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Network error retrieving hospitals for batch {batch_id}: {str(e)} ({elapsed_time:.2f}s)")
            raise Exception(f"Network error retrieving hospitals: {str(e)}")
    
    def delete_batch(self, batch_id):
        """
        Delete all hospitals in the given batch
        
        Args:
            batch_id (str): UUID of the batch to delete
        
        Returns:
            dict: The deletion response
        
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/hospitals/batch/{batch_id}"
        start_time = time.time()
        
        self.logger.info(f"Deleting hospitals in batch {batch_id}")
        
        try:
            self.logger.debug(f"Sending DELETE request to {url}")
            response = self.session.delete(url)
            elapsed_time = time.time() - start_time
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', response.text)
                except:
                    error_msg = response.text
                    
                if response.status_code == 404:
                    self.logger.error(f"Batch {batch_id} not found when attempting to delete ({elapsed_time:.2f}s)")
                    raise Exception(f"Batch {batch_id} not found")
                else:
                    self.logger.error(f"Failed to delete batch {batch_id}: {error_msg} (Status: {response.status_code}, {elapsed_time:.2f}s)")
                    raise Exception(f"Failed to delete batch: {error_msg} (Status: {response.status_code})")
            
            response_data = response.json()
            deleted_count = response_data.get('deleted_count', 0)
            self.logger.info(f"Deleted {deleted_count} hospitals from batch {batch_id} ({elapsed_time:.2f}s)")
            return response_data
            
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Network error deleting batch {batch_id}: {str(e)} ({elapsed_time:.2f}s)")
            raise Exception(f"Network error deleting batch: {str(e)}")
        