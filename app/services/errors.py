class CustomerNotFound(Exception):
    def __init__(self, customer_id: str) -> None:
        super().__init__(f"Customer {customer_id} not found")
        self.customer_id = customer_id
