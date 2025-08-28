"""
Common document number generation service
Generates document numbers in format: [PREFIX]-[street_num]-[company_code]-[sequence]
"""

from typing import Optional
import re

class DocumentNumberService:
    """Service for generating document numbers with consistent format"""
    
    def __init__(self, db):
        self.db = db
        
        # Define prefixes for different document types
        self.PREFIXES = {
            'invoice': 'INV',
            'estimate': 'EST',
            'plumber_report': 'PLM',
            'insurance_estimate': 'INS'
        }
        
        # Map document types to their database tables
        self.TABLE_MAP = {
            'invoice': 'general_invoice',
            'estimate': 'estimate',  # Corrected table name
            'plumber_report': 'plumber_reports',
            'insurance_estimate': 'insurance_estimates'
        }
    
    def extract_street_number(self, address: str) -> str:
        """Extract street number from address and format to 4 digits"""
        if not address:
            return "0000"
            
        # Find all numbers in the address
        numbers = re.findall(r'\d+', address)
        
        if numbers:
            # Use the first number found (usually the street number)
            street_num = numbers[0]
            # Pad with zeros to make it 4 digits
            return street_num.zfill(4)[-4:]  # Take last 4 digits if longer than 4
        else:
            # No number found, use 0000
            return "0000"
    
    def get_document_count_for_company(self, document_type: str, company_code: str) -> int:
        """Get the count of documents for a specific company"""
        try:
            table_name = self.TABLE_MAP.get(document_type)
            if not table_name:
                return 0
            
            # Get the field name for document number (might vary by table)
            number_field = self._get_number_field(document_type)
            prefix = self.PREFIXES.get(document_type, 'DOC')
            
            # Query documents that match the company code pattern
            response = self.db.table(table_name).select(number_field).like(
                number_field, 
                f'{prefix}-%-{company_code}-%'
            ).execute()
            
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error counting {document_type} for company {company_code}: {e}")
            return 0
    
    def _get_number_field(self, document_type: str) -> str:
        """Get the field name for document number based on document type"""
        field_map = {
            'invoice': 'invoice_number',
            'estimate': 'estimate_number',
            'plumber_report': 'report_number',
            'insurance_estimate': 'estimate_number'
        }
        return field_map.get(document_type, 'document_number')
    
    def generate_document_number(
        self, 
        document_type: str,
        client_address: str, 
        company_code: str
    ) -> str:
        """
        Generate document number in format: [PREFIX]-[street_num]-[company_code]-[sequence]
        
        Args:
            document_type: Type of document (invoice, estimate, plumber_report, etc.)
            client_address: Client's street address
            company_code: 4-character company code
            
        Returns:
            Generated document number
        """
        # Get prefix for document type
        prefix = self.PREFIXES.get(document_type, 'DOC')
        
        # Extract street number
        street_num = self.extract_street_number(client_address)
        
        # Get next sequence number for this company
        count = self.get_document_count_for_company(document_type, company_code)
        sequence = count + 1
        
        # Format document number
        document_number = f"{prefix}-{street_num}-{company_code}-{sequence}"
        
        # Check if this exact number exists (unlikely but possible)
        if self._number_exists(document_type, document_number):
            # Number exists, increment sequence
            sequence += 1
            document_number = f"{prefix}-{street_num}-{company_code}-{sequence}"
        
        return document_number
    
    def _number_exists(self, document_type: str, document_number: str) -> bool:
        """Check if a document number already exists"""
        try:
            table_name = self.TABLE_MAP.get(document_type)
            if not table_name:
                return False
                
            number_field = self._get_number_field(document_type)
            
            response = self.db.table(table_name).select('id').eq(
                number_field, 
                document_number
            ).execute()
            
            return bool(response.data)
        except:
            return False
    
    def get_company_code(self, company_name: str) -> Optional[str]:
        """Get company code by company name"""
        try:
            response = self.db.table('companies').select('company_code').eq(
                'name', 
                company_name
            ).execute()
            
            if response.data and response.data[0].get('company_code'):
                return response.data[0]['company_code']
            return None
        except Exception as e:
            print(f"Error fetching company code for {company_name}: {e}")
            return None
    
    def generate_temp_company_code(self, company_name: str) -> str:
        """Generate a temporary company code for custom companies"""
        import random
        import string
        
        # Extract initials from company name
        words = company_name.split()
        if len(words) >= 2:
            # Use first letter of first two words
            code = words[0][0].upper() + words[1][0].upper()
        elif len(words) == 1 and len(words[0]) >= 2:
            # Use first two letters of single word
            code = words[0][:2].upper()
        else:
            # Use random letters if name is too short
            code = random.choice(string.ascii_uppercase) + random.choice(string.ascii_uppercase)
        
        # Add 'C' to indicate custom company and a random digit
        code = 'C' + code + str(random.randint(0, 9))
        
        return code