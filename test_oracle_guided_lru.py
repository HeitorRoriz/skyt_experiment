"""
Test Oracle-Guided Transformer on lru_cache

Verifies that the transformer can handle algorithmic diversity.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.transformations.behavioral.oracle_guided_transformer import OracleGuidedTransformer
from src.foundational_properties import FoundationalProperties


# Canon implementation (doubly-linked list)
canon_code = """
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add(node)
            return node.value
        return -1

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self._remove(self.cache[key])
        node = Node(key, value)
        self.cache[key] = node
        self._add(node)
        if len(self.cache) > self.capacity:
            lru = self.tail.prev
            self._remove(lru)
            del self.cache[lru.key]
"""

# Alternative implementation (simple list - 70% of outputs)
simple_list_code = """
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.order = []

    def get(self, key: int) -> int:
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return -1

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache[key] = value
            self.order.remove(key)
        else:
            if len(self.cache) >= self.capacity:
                lru = self.order.pop(0)
                del self.cache[lru]
            self.cache[key] = value
        self.order.append(key)
"""


def test_transformation():
    """Test oracle-guided transformation"""
    
    print("="*70)
    print("TESTING ORACLE-GUIDED TRANSFORMER ON LRU_CACHE")
    print("="*70)
    
    # Initialize transformer
    transformer = OracleGuidedTransformer(distance_threshold=0.15)
    transformer.enable_debug()
    
    # Calculate initial distance
    props_extractor = FoundationalProperties()
    simple_props = props_extractor.extract_transformation_properties(simple_list_code)
    canon_props = props_extractor.extract_transformation_properties(canon_code)
    initial_distance = props_extractor.calculate_transformation_distance(simple_props, canon_props)
    
    print(f"\nInitial distance: {initial_distance:.3f}")
    print(f"Threshold: {transformer.distance_threshold}")
    print(f"\nSimple list implementation (23 lines)")
    print(f"Canon doubly-linked list implementation (45 lines)")
    
    # Test if it can transform
    print("\n" + "-"*70)
    print("Testing can_transform...")
    can_transform = transformer.can_transform(simple_list_code, canon_code)
    print(f"Can transform: {can_transform}")
    
    if can_transform:
        print("\n" + "-"*70)
        print("Applying transformation...")
        result = transformer.transform(simple_list_code, canon_code)
        
        print(f"\nTransformation success: {result.success}")
        print(f"Distance improvement: {result.distance_improvement:.3f}")
        
        if result.success:
            # Verify result matches canon
            result_props = props_extractor.extract_transformation_properties(result.transformed_code)
            final_distance = props_extractor.calculate_transformation_distance(result_props, canon_props)
            
            print(f"Final distance: {final_distance:.3f}")
            print(f"\n✅ Positive rescue: {initial_distance:.3f} → {final_distance:.3f}")
            
            # Test idempotency
            print("\n" + "-"*70)
            print("Testing idempotency...")
            result2 = transformer.transform(result.transformed_code, canon_code)
            
            if result.transformed_code == result2.transformed_code:
                print("✅ IDEMPOTENT: Transformation is stable")
            else:
                print("❌ NOT IDEMPOTENT: Transformation unstable!")
            
            # Verify transformation reached canon
            if final_distance < 0.01:
                print("\n✅ REACHED CANON: Distance < 0.01")
            else:
                print(f"\n⚠️  Distance still {final_distance:.3f} (didn't fully converge)")
        
        else:
            print(f"\n⚠️  Transformation failed: {result.error_message}")
    
    else:
        print("\n⚠️  Cannot transform (distance too low or other issue)")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_transformation()
