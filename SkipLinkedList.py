import math

class Node:
    def __init__(self, val):
        # initializes from a string: either an integer (1) or an integer with a skip pointer (2^9)
        val_clean = val.strip()
        if '^' in val_clean:
            self.val, self.skip = val_clean.split("^")
        else:
            self.val = val_clean
            self.skip = None  # Skip pointer
        self.next = None

    def forward_node(self, other_node):
        '''
        chooses to move either to the next node, or the skip pointer
        depending on the value of the other node
        returns either the next node or the skip node, or none if both are not available
        '''
        if self.skip and int(self.skip.val) <= int(other_node.val):
            return self.skip
        elif self.next:
            return self.next
        else:
            return None



    def __str__(self):
        if self.skip is not None:
            return f"{self.val}^{self.skip.val}"
        else:
            return str(self.val)

    def __repr__(self):
        return str(self)


class SkipLinkedList:
    def __init__(self, save_string = None):
        # Either initializes from nothing or from a save string
        # Can also initialize from list of ints
        self.head = None
        self.tail = None
        if isinstance(save_string, list):
            self.from_list(save_string)
        elif not save_string:
            self.length = 0
        else:
            self.from_string(save_string)

    def from_string(self, s):
        doc_ids = s.split(" ")
        for id in doc_ids:
            self.insert(id)
        self.stitch_skips()

    def from_list(self, save_list):
        self.length = len(save_list)
        for id in save_list:
            self.insert(str(id))
        self.update_skip_pointers()

    def stitch_skips(self):
        if not self.head:
            return

        current = self.head
        while current:
            if current.skip is not None:
                # Find the node to which the skip pointer should point
                target_val = int(current.skip)
                target_node = self.find_node_by_value(target_val)

                if target_node:
                    current.skip = target_node
                else:
                    # If the target node is not found, set skip pointer to None
                    current.skip = None

            current = current.next

    def find_node_by_value(self, value):
        current = self.head
        while current:
            if int(current.val) == value:
                return current
            elif int(current.val) > value:
                return None
            current = current.next
        return None

    def insert(self, val):
        # only allow insertion at tail: nodes should already be sorted
        new_node = Node(val)
        if not self.head:
            self.head = new_node
            self.tail = new_node
            self.length = 1
            return

        else:
            self.tail.next = new_node
            self.tail = new_node
            self.length += 1

    def update_skip_pointers(self):
        if self.length <= 3:
            return

        current = self.head
        prev = self.head
        skip_distance = round(math.sqrt(self.length))

        while True:
            prev = current
            for i in range(skip_distance):
                current = current.next
                if not current:
                    return
            prev.skip = current
            if not current.next:
                break

    def merge(self, other_skip_linked_list):
        merged_list = SkipLinkedList()

        # pointers for both lists
        current_self = self.head
        current_other = other_skip_linked_list.head

        # traverse both linked lists until one of them becomes empty
        while current_self and current_other:
            if int(current_self.val) < int(current_other.val):
                merged_list.insert(current_self.val)
                current_self = current_self.next
            elif int(current_self.val) > int(current_other.val):
                merged_list.insert(current_other.val)
                current_other = current_other.next
            else:
                # if equal, takes one value, discards the other and moves both pointers
                merged_list.insert(current_self.val)
                current_self = current_self.next
                current_other = current_other.next

        # add all remaining in one list or the other
        while current_self:
            merged_list.insert(current_self.val)
            current_self = current_self.next
        while current_other:
            merged_list.insert(current_other.val)
            current_other = current_other.next

        # add skip pointers for new list
        merged_list.update_skip_pointers()
        return merged_list

    def OR(self, other_skip_linked_list):
        '''
        same as self.merge(), but doesn't add skip pointers (faster)
        does an OR operation between self and other list
        returns a merge of the two lists
        '''
        merged_list = SkipLinkedList()

        # pointers for both lists
        current_self = self.head
        current_other = other_skip_linked_list.head

        # traverse both linked lists until one of them becomes empty
        while current_self and current_other:
            if int(current_self.val) < int(current_other.val):
                merged_list.insert(current_self.val)
                current_self = current_self.next
            elif int(current_self.val) > int(current_other.val):
                merged_list.insert(current_other.val)
                current_other = current_other.next
            else:
                # if equal, takes one value, discards the other and moves both pointers
                merged_list.insert(current_self.val)
                current_self = current_self.next
                current_other = current_other.next

        # add all remaining in one list or the other
        while current_self:
            merged_list.insert(current_self.val)
            current_self = current_self.next
        while current_other:
            merged_list.insert(current_other.val)
            current_other = current_other.next

        return merged_list

    def AND(self, other_skip_linked_list):
        """
        performs AND operation between self and other list
        returns the intersection of two lists
        """
        intersection = SkipLinkedList()
        current1 = self.head
        current2 = other_skip_linked_list.head

        while current1 and current2:
            if current1.val == current2.val:
                intersection.insert(current1.val)
                current1 = current1.forward_node(current2)
                current2 = current2.forward_node(current1)
            elif int(current1.val) < int(current2.val):
                current1 = current1.forward_node(current2)
            else:
                current2 = current2.forward_node(current1)

        return intersection

    def NOT(self, other_skip_linked_list):
        """
        performs a NOT operation where self is assumed to be the superset
        returns a list of values in self but not in other list
        """
        result = SkipLinkedList()
        current1 = self.head
        current2 = other_skip_linked_list.head

        while current1:
            if not current2 or int(current1.val) < int(current2.val):
                result.insert(current1.val)
                current1 = current1.next
            elif current1.val == current2.val:
                current1 = current1.forward_node(current2)
                current2 = current2.forward_node(current1)
            elif int(current1.val) > int(current2.val):
                current2 = current2.forward_node(current1)

        return result

    def get_value_string(self):
        '''
        only values (no pointers)
        '''
        doc_ids = []
        current = self.head
        while current:
            doc_ids.append(str(current.val))
            current = current.next
        return " ".join(doc_ids)

    def __str__(self):
        doc_ids = []
        current = self.head
        while current:
            doc_ids.append(str(current))
            current = current.next
        return " ".join(doc_ids)

    def __repr__(self):
        return str(self)

