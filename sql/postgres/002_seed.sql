INSERT INTO customers (customer_id, name, segment, region, account_owner, salesforce_id, contact_name, contact_phone, address) VALUES
    ('C-1001', 'Acme Aerospace', 'Enterprise', 'NA-East', 'jlee', '001A000001', 'Dana Whitfield', '+1 (617) 555-0142', '200 Harbor Way, Boston, MA 02210'),
    ('C-1002', 'Blue Ridge Health', 'Enterprise', 'NA-East', 'mpatel', '001A000002', 'Marcus Ellery', '+1 (704) 555-0178', '4100 Piedmont Row Dr, Charlotte, NC 28210'),
    ('C-1003', 'Cardinal Logistics', 'Mid-Market', 'NA-Central', 'jlee', '001A000003', 'Priya Raman', '+1 (312) 555-0119', '875 W Lake St, Chicago, IL 60607'),
    ('C-1004', 'Delta Fintech', 'Mid-Market', 'EMEA', 'asmith', '001A000004', 'Sofia Lindqvist', '+44 20 7946 0321', '30 Finsbury Square, London EC2A 1AG, UK'),
    ('C-1005', 'Evergreen Retail', 'Commercial', 'NA-West', 'mpatel', '001A000005', 'Tom Okafor', '+1 (503) 555-0164', '1220 NW Lovejoy St, Portland, OR 97209')
ON CONFLICT (customer_id) DO UPDATE SET
    contact_name  = COALESCE(customers.contact_name,  EXCLUDED.contact_name),
    contact_phone = COALESCE(customers.contact_phone, EXCLUDED.contact_phone),
    address       = COALESCE(customers.address,       EXCLUDED.address);
