from product import ProductType, Product, Package
from vector2d import Vector2D
from collections import deque

class Organization(object):
	'''
	Class representing a 'place' in the world, such as a factory or store.
	Virtual class, inherited only by Factory so far.
	'''
	name = 'Organization'
	inher_order = ['Mine', 'Factory', 'Customer Point']
	
	def __init__(self, position):
		assert isinstance(position, Vector2D), 'position not a Vector2D.'
		self.position = position
		return None

	def single_round(self):
		raise Exception('Why did I get called? (Organization.single_round)')
	

class Mine(Organization):
	'''
	Class representing an organization that exclusively produces materials,
	without requiring any supplies on input.
	'''
	name = 'Mine'
	
	def __init__(self, product_type, capacity, position):
		'''
		Params: same as Factory (see below).
		'''
		Organization.__init__(self, position)
		
		assert isinstance(product_type, ProductType),\
			'product_type not a ProductType'
		self.product_type = product_type
		
		assert isinstance(capacity, int), 'capacity not an int.'
		self.capacity = int(capacity/self.product_type.difficulty)
		
		# list of customers for products
		self.customers = dict()
		
		# output queue
		self.output = deque()

		self.production = 0	# stat value; total number of produced items	
		return None
	
	def __repr__(self):
		return '<Mine {0} at {1}, cap. {2}, producing {3}>'.format(
			hex(id(self))[-5:], self.position, self.capacity,\
			self.product_type.name)
	
	def __str__(self):
		return 'Mine at {0} producing {1}'.format(self.position,
			self.product_type)
		
	def produce(self):
		'''
		Method for handling producing during one time unit.
		'''
		for p in range(self.capacity):
			self.output.append(Product(self.product_type))
			self.production += 1
		return None
	
	def send(self, package, customer):
		dist = int((self.position - customer.position).length)
		while len(customer.input) < dist:
			customer.input.append(list())
		customer.input[dist - 1].append(package)
		return None
	def export(self):
		'''
		Method handling production export to customers.
		Current system: production is divided among customers in ratios
		equivalent to their product requirements.
		'''
		if len(self.customers) == 0:
			return None
		total_requirements = sum(self.customers.values())
		production_available = len(self.output)
		for cust in self.customers:
			package = Package()
			for i in range(int(production_available * \
				self.customers[cust]/total_requirements)):
				package.pack(self.output.popleft())
			self.send(package, cust)
		return None
	
	def single_round(self, temp_capacity):
		tmp = self.capacity
		self.capacity = temp_capacity
		self.produce()
		self.export()
		self.capacity = tmp
		return None


class Factory(Organization):
	'''
	Class representing a single manufacturing unit.
	The factory is placed on a certain position in the game world,
	and manufactures a product based on its specification.
	'''
	name = 'Factory'

	def __init__(self, product_type, capacity, position):
		'''
		Params:
			-- product_type - produced ProductType ref
			-- capacity - int, production per time unit
			-- position - 2D Vector that positions factory in game world
		'''
		Organization.__init__(self, position)
		
		assert isinstance(product_type, ProductType),\
			'product_type not a ProductType'
		self.product_type = product_type
		
		assert isinstance(capacity, int), 'capacity not an int.'
		self.capacity = int(capacity/self.product_type.difficulty)
		
		# storage of required materials
		self.storage = dict()
		for item in self.product_type.requirements:
			self.storage[item] = 0
		
		# list of factories supplying the materials
		self.suppliers = dict()
		
		# supply input queue
		self.input = deque()
		
		# list of customers for products
		self.customers = dict()
		
		# output queue
		self.output = deque()
		
		self.production = 0 # stat value; total number of produced items
		return None
	
	def __repr__(self):
		return '<Factory {0} at {1}, cap. {2} product {3}>'.format(
			hex(id(self))[-5:], self.position, self.capacity,
			self.product_type.name)
	
	def __str__(self):
		return 'Factory at {0} producing {1}'.format(self.position,
			self.product_type)
	
	def update_suppliers(self, world):
		'''
		Method for updating the refs to factories supplying required materials.
		Param world -- ref to world object
		'''
		for m in self.storage:
			self.suppliers[m] = world.product_origin[m]
			self.suppliers[m].customers[self] =\
				self.product_type.requirements[m]
		return None
	
	def material_sufficient(self):
		'''
		Aux. method returning the number of product items that could
		be produced with current materials in storage (not taking into account
		the capacity of the factory).
		'''
		return int(min([self.storage[i]/self.product_type.requirements[i]\
			for i in self.storage]))
	
	def accept_supplies(self):
		'''
		Method for accepting the supplies, i.e. moving them from the first
		place in input queue into the storage.
		'''
		if len(self.input) == 0: # no supplies available
			 return None
		incoming_load = self.input.popleft()
		for package in incoming_load:
			while len(package) > 0:
				item = package.unpack()
				assert item.product_type in self.storage,\
					'Factory with requirements {0}'.format(list(
						self.storage.keys())) + ' accepted spam: {1}.'.\
							format(self, item)
				self.storage[item.product_type] += 1
		return None
		
	def produce(self):
		'''
		Method for handling producing during one time unit.
		'''
		if len(self.storage) > 0:
			amount = min([self.material_sufficient(), self.capacity])
		else:
			amount = self.capacity # When no materials are required.
		
		for item in self.product_type.requirements:
			self.storage[item] -= amount * self.product_type.requirements[item]
		for p in range(amount):
			self.output.append(Product(self.product_type))
			self.production += 1
		return None
	
	def send(self, package, customer):
		dist = int((self.position - customer.position).length)
		while len(customer.input) < dist:
			customer.input.append(list())
		customer.input[dist - 1].append(package)
		return None
	def export(self):
		'''
		Method handling production export to customers.
		Current system: production is divided among customers in ratios
		equivalent to their product requirements.
		'''
		if len(self.customers) == 0:
			return None
		total_requirements = sum(self.customers.values())
		production_available = len(self.output)
		for cust in self.customers:
			package = Package()
			for i in range(int(production_available * \
				self.customers[cust]/total_requirements)):
				package.pack(self.output.popleft())
			self.send(package, cust)
		return None
	
	def single_round(self, temp_capacity):
		'''
		Method for handling actions taking place in a single time unit.
		'''
		tmp = self.capacity
		self.capacity = temp_capacity
		self.accept_supplies()
		self.produce()
		self.export()
		self.capacity = tmp
		return None


class CustomerPoint(Organization):
	'''
	Class representing a consumer point (e.g., a market) as an organization
	that only accepts products without producing anything.
	The storage keeps track of input goods so far (for statistical purposes).
	'''
	name = 'Customer Point'
	def __init__(self, product_type, capacity, position):
		'''
		Params:
			-- product_type - produced ProductType ref
			-- capacity - int, production per time unit
			-- position - 2D Vector that positions factory in game world
		'''
		Organization.__init__(self, position)
		
		assert isinstance(product_type, ProductType),\
			'product_type not a ProductType'
		self.product_type = product_type
		
		assert isinstance(capacity, int), 'capacity not an int.'
		self.capacity = capacity
		
		# storage of accepted materials
		self.storage = dict()
		self.storage[product_type] = 0
		
		# list of factories supplying the materials
		self.suppliers = dict()
		
		# supply input queue
		self.input = deque()
		return None
	
	def __repr__(self):
		return '<CustomerPoint {0} at {1}, cap. {2}, accepting {3}>'.format(
			hex(id(self))[-5:], self.position, self.capacity, self.product_type)
	
	def __str__(self):
		return 'CustomerPoint at {0} accepting {1}'.format(self.position,
			self.product_type)
	
	def update_suppliers(self, world):
		'''
		Method for updating the refs to factories supplying required materials.
		Param world -- ref to world object
		'''
		self.suppliers[self.product_type] = \
			world.product_origin[self.product_type]
		self.suppliers[self.product_type].customers[self] = self.capacity
		return None
	
	def accept_supplies(self):
		'''
		Method for accepting the supplies, i.e. moving them from the first
		place in input queue into the storage.
		'''
		if len(self.input) == 0: # no supplies available
			 return None
		incoming_load = self.input.popleft()
		for package in incoming_load:
			while len(package) > 0:
				item = package.unpack()
				assert item.product_type in self.storage,\
					'Factory with requirements {0}'.format(list(
						self.storage.keys())) + ' accepted spam: {1}.'.\
							format(self, item)
				self.storage[item.product_type] += 1
		return None
	
	def single_round(self, temp_capacity):
		'''
		Method for handling actions taking place in a single time unit.
		'''
		tmp = self.capacity
		self.capacity = temp_capacity
		self.accept_supplies()
		self.capacity = tmp
		return None
