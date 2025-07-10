from collections import defaultdict
import random

class AdvancedNobetDagitim:
    def __init__(self, population_size=50, generations=100, initial_mutation_rate=0.1, max_shifts=2):
        self.penalty_weights = {
            'overload': 100,   # aşırı yüklenme cezası
            'inequality': 200,  # Eşitsiz dağılım
            'unassigned': 220,   # Atanamayan dersler
            'no_duty': 300,     # Hiç nöbet almayan öğretmen
            'conflict': 1000    # Çakışan nöbetler
        }
        self.population_size = population_size
        self.generations = generations
        self.initial_mutation_rate = initial_mutation_rate
        self.current_mutation_rate = initial_mutation_rate
        self.max_shifts = max_shifts
        # Uyarlanabilir parametreler
        self.mutation_rate_min = 0.01
        self.mutation_rate_max = 0.5
        self.adaptation_factor = 0.95  # Her nesilde mutasyon oranını değiştirme faktörü
    
    def optimize(self, available_teachers, absent_teachers):
        self.availability = self.prepare_availability(available_teachers)
        self.absent_classes = self.flatten_absent(absent_teachers)
        self.teachers = available_teachers
        self.teacher_ids = [t['ogretmen_id'] for t in available_teachers]
        
        population = [self.create_individual() for _ in range(self.population_size)]
        best_penalty = float('inf')
        stagnation_count = 0
        
        for generation in range(self.generations):
            population.sort(key=lambda x: self.calculate_penalty(x))
            current_best_penalty = self.calculate_penalty(population[0])
            
            # Uyarlanabilir mutasyon oranı güncelleme
            if current_best_penalty < best_penalty:
                best_penalty = current_best_penalty
                stagnation_count = 0
                # İyileşme varsa mutasyon oranını biraz artır
                self.current_mutation_rate = min(
                    self.mutation_rate_max,
                    self.current_mutation_rate * (1 + (1 - self.adaptation_factor))
                )
            else:
                stagnation_count += 1
                # Durgunluk varsa mutasyon oranını artır
                if stagnation_count > 5:
                    self.current_mutation_rate = min(
                        self.mutation_rate_max,
                        self.current_mutation_rate * (1 + (1 - self.adaptation_factor))
                    )
                else:
                    # Normal şartlarda mutasyon oranını kademeli azalt
                    self.current_mutation_rate = max(
                        self.mutation_rate_min,
                        self.current_mutation_rate * self.adaptation_factor
                    )
            
            new_population = [population[0]]  # Elitizm: En iyi çözümü koru

            while len(new_population) < self.population_size:
                parent = random.choice(population[:10])  # En iyi 10'dan ebeveyn seç
                child = self.mutate(parent)
                new_population.append(child)

            population = new_population
        
        best_solution = min(population, key=lambda x: self.calculate_penalty(x))
        return self.format_solution(best_solution)
    
    def mutate(self, individual):
        for assignment in individual['assignments']:
            if random.random() < self.current_mutation_rate:  # Uyarlanabilir oran kullan
                eligible_teachers = [
                    t_id for t_id in self.teacher_ids 
                    if self.availability[t_id][assignment['hour']] 
                    and assignment['hour'] not in individual['teacher_schedule'][t_id]
                    and individual['teacher_counts'][t_id] < self.max_shifts
                ]
                if eligible_teachers:
                    new_teacher = random.choice(eligible_teachers)
                    old_teacher = assignment['teacher_id']
                    individual['teacher_counts'][old_teacher] -= 1
                    individual['teacher_schedule'][old_teacher].remove(assignment['hour'])
                    assignment['teacher_id'] = new_teacher
                    individual['teacher_counts'][new_teacher] += 1
                    individual['teacher_schedule'][new_teacher].add(assignment['hour'])
        return individual
    
    def create_individual(self):
        solution = {
            'assignments': [], 
            'teacher_counts': defaultdict(int), 
            'teacher_schedule': defaultdict(set)
        }
        for class_info in self.absent_classes:
            eligible_teachers = [t_id for t_id in self.teacher_ids 
                                 if self.availability[t_id][class_info['hour']] 
                                 and solution['teacher_counts'][t_id] < self.max_shifts]  # aşırı yüklenme engeli
            random.shuffle(eligible_teachers)
            for teacher_id in eligible_teachers:
                if class_info['hour'] not in solution['teacher_schedule'][teacher_id]:
                    solution['assignments'].append({
                        'hour': class_info['hour'],
                        'class': class_info['class'],
                        'teacher_id': teacher_id,
                        'absent_teacher_id': class_info['absent_teacher_id']
                    })
                    solution['teacher_counts'][teacher_id] += 1
                    solution['teacher_schedule'][teacher_id].add(class_info['hour'])
                    break
        return solution

    def calculate_penalty(self, solution):
        penalty = 0
        counts = list(solution['teacher_counts'].values())
        if counts:
            penalty += (max(counts) - min(counts)) * self.penalty_weights['inequality']
        penalty += (len(self.absent_classes) - len(solution['assignments'])) * self.penalty_weights['unassigned']
        penalty += len([t_id for t_id in self.teacher_ids if solution['teacher_counts'][t_id] == 0]) * self.penalty_weights['no_duty']
        
        # aşırı yüklenme cezası (max nöbet sayısını aşanlar için)
        overload_count = sum(max(0, count - self.max_shifts) for count in counts)
        penalty += overload_count * self.penalty_weights['overload']
        
        conflicts = 0
        teacher_hours = defaultdict(set)
        for assignment in solution['assignments']:
            hour = assignment['hour']
            teacher_id = assignment['teacher_id']
            if hour in teacher_hours[teacher_id]:
                conflicts += 1
            else:
                teacher_hours[teacher_id].add(hour)
        penalty += conflicts * self.penalty_weights['conflict']
        
        return penalty

    def format_solution(self, solution):
        assigned_classes = {(a['hour'], a['class']) for a in solution['assignments']}
        all_classes = {(c['hour'], c['class']) for c in self.absent_classes}
        unassigned = [{'hour': c['hour'], 'class': c['class'], 'absent_teacher_id': c['absent_teacher_id']} 
                     for c in self.absent_classes 
                     if (c['hour'], c['class']) not in assigned_classes]
        
        return {
            'assignments': solution['assignments'],
            'unassigned': unassigned,
            'teacher_counts': dict(solution['teacher_counts']),
            'teacher_schedule': {k: list(v) for k, v in solution['teacher_schedule'].items()},
            'penalty': self.calculate_penalty(solution)
        }

    def prepare_availability(self, teachers):
        availability = {}
        for teacher in teachers:
            teacher_id = teacher['ogretmen_id']
            busy_hours = set(teacher['dersleri'].keys())
            availability[teacher_id] = {hour: (hour not in busy_hours) for hour in range(1, 9)}
        return availability
    
    def flatten_absent(self, absent_teachers):
        return [{'hour': int(h), 'class': c, 'absent_teacher_id': t['ogretmen_id']} 
                for t in absent_teachers for h, c in t['dersleri'].items()]
