import pandas as pd


class NodeCreator:

    def __init__(self, final_df):
        self.final_df = final_df
        self.unique_nodes = set()
        self.unique_relations = set()
        self.node_properties = set()
        self.same_as_mapping = {
            'university': {
                'Politechnika Warszawska': 'Warsaw University of Technology',
            },
            'city': {
                'Warszawa': 'Warsaw',
                # Add other city mappings here
            },
            'country': {
                'Polska': 'Poland',
                # Add other country mappings here
            }
        }

    def create_node(self, node_name, node_type, source, language):
        node = {
            'Node_name': node_name,
            'Node_type': node_type,
            'source': source,
            'language': language
        }
        self.unique_nodes.add(tuple(node.items()))

    def create_relation(self, source, label, target):
        relation = {
            'source': source,
            'label': label,
            'target': target
        }
        self.unique_relations.add(tuple(relation.items()))

    def create_property(self, node_name, property_name, property_value):
        node_property = {
            'node_name': node_name,
            'property_name': property_name,
            'property_value': property_value
        }
        self.node_properties.add(tuple(node_property.items()))

    def process_data(self):
        for _, row in self.final_df.iterrows():
            self.create_node(row['University_name'], 'university', row['Source'], row['Language'])
            self.create_node(row['City'], 'city', row['City'], row['Language'])
            self.create_node(row['Country'], 'country', row['Country'], row['Language'])

            # Field of study
            self.create_node(row['Field_of_study'], 'field', row['Field_of_study'], row['Language'])

            # Faculty is a division of one or few fields of study
            self.create_node(row['Faculty'], 'faculty', row['Faculty'], row['Language'])

            # Subject is single subject
            self.create_node(row['Subject'], 'subject', row['Subject'], row['Language'])

            # Specialization is a branch of field of study, division of few subjects
            self.create_node(row['Specialization'], 'specialization', row['Specialization'], row['Language'])

            self.create_relation(row['University_name'], 'IS_LOCATED', row['City'])
            self.create_relation(row['City'], 'IS_PART_OF', row['Country'])
            self.create_relation(row['Faculty'], 'IS_PART_OF', row['University_name'])
            self.create_relation(row['Field_of_study'], 'IS_PART_OF', row['Faculty'])
            self.create_relation(row['Subject'], 'IS_PART_OF', row['Field_of_study'])

            self.create_relation(row['Specialization'], 'IS_PART_OF', row['Field_of_study'])
            self.create_relation(row['Subject'], 'IS_PART_OF', row['Specialization'])

            # creating SAME AS RELATIONS
            if row['Language'] == 'Polish':
                if row['University_name'] in self.same_as_mapping['university']:
                    self.create_relation(row['University_name'], 'SAME_AS',
                    self.same_as_mapping['university'][row['University_name']])
                if row['City'] in self.same_as_mapping['city']:
                    self.create_relation(row['City'], 'SAME_AS',
                    self.same_as_mapping['city'][row['City']])
                if row['Country'] in self.same_as_mapping['country']:
                    self.create_relation(row['Country'], 'SAME_AS',
                    self.same_as_mapping['country'][row['Country']])

            self.create_property(row['Subject'], 'ECTS_subject_weight', row['Ect'])
            self.create_property(row['Field_of_study'], 'level_details', row['Level'])
            self.create_property(row['Subject'], 'semester_details', row['Semester'])
            self.create_property(row['Subject'], 'syllabus_details', row['Syllabus'])

        self.unique_nodes = [dict(node) for node in self.unique_nodes]
        self.unique_relations = [dict(relation) for relation in self.unique_relations]
        self.node_properties = [dict(properties) for properties in self.node_properties]

    def save_data_to_csv(self):
        nodes_df = pd.DataFrame(self.unique_nodes)
        relations_df = pd.DataFrame(self.unique_relations)
        node_properties_df = pd.DataFrame(self.node_properties)

        nodes_df.to_csv('nodes.csv', index=False)
        relations_df.to_csv('relations.csv', index=False)
        node_properties_df.to_csv('node_properties.csv', index=False)
