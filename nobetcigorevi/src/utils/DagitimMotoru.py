from collections import defaultdict
import random


class AdvancedNobetDagitim:
    def __init__(self, population_size=250, generations=200, initial_mutation_rate=0.1, max_shifts=2):
        self.penalty_weights = {
            'overload': 100,       # aşırı yüklenme
            'inequality': 200,     # eşitsiz dağılım
            'unassigned': 250,     # atanamayan ders
            'no_duty': 400,        # hiç nöbeti olmayan
            'conflict': 1000,      # çakışan nöbet
            'unfair': 500,         # istatistiksel adaletsizlik
            'same_location': 600   # aynı nöbet yerinde ardışık atama cezası
        }

        self.population_size = population_size
        self.generations = generations
        self.initial_mutation_rate = initial_mutation_rate
        self.current_mutation_rate = initial_mutation_rate
        self.max_shifts = max_shifts

        # Uyarlanabilir mutasyon
        self.mutation_rate_min = 0.01
        self.mutation_rate_max = 0.5
        self.adaptation_factor = 0.95

        # NobetIstatistik verisi
        self.teacher_stats = {}

    # ======================================================
    # 🔹 Yeni: NobetIstatistik verisini yükle
    # ======================================================
    def set_teacher_statistics(self, stats_dict):
        """
        stats_dict = {
            ogretmen_id: {
                'haftalik_ortalama': float,
                'agirlikli_puan': float,
                'toplam_nobet': int,
                'hafta_sayisi': int,
                'son_nobet_tarihi': datetime,
                'son_nobet_yeri': str
            }
        }
        """
        self.teacher_stats = stats_dict or {}

    # ======================================================
    # 🔹 Ana optimize fonksiyonu
    # ======================================================
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

            if current_best_penalty < best_penalty:
                best_penalty = current_best_penalty
                stagnation_count = 0
                self.current_mutation_rate = min(
                    self.mutation_rate_max,
                    self.current_mutation_rate * (1 + (1 - self.adaptation_factor))
                )
            else:
                stagnation_count += 1
                if stagnation_count > 5:
                    self.current_mutation_rate = min(
                        self.mutation_rate_max,
                        self.current_mutation_rate * (1 + (1 - self.adaptation_factor))
                    )
                else:
                    self.current_mutation_rate = max(
                        self.mutation_rate_min,
                        self.current_mutation_rate * self.adaptation_factor
                    )

            new_population = [population[0]]  # Elitizm: en iyi bireyi koru
            while len(new_population) < self.population_size:
                parent = random.choice(population[:10])
                child = self.mutate(parent)
                new_population.append(child)
            population = new_population

        best_solution = min(population, key=lambda x: self.calculate_penalty(x))
        return self.format_solution(best_solution)

    # ======================================================
    # 🔹 Mutasyon: adaletli ağırlıklandırılmış seçim
    # ======================================================
    def mutate(self, individual):
        for assignment in individual['assignments']:
            if random.random() < self.current_mutation_rate:
                eligible_teachers = [
                    t_id for t_id in self.teacher_ids
                    if self.availability[t_id][assignment['hour']]
                    and assignment['hour'] not in individual['teacher_schedule'][t_id]
                    and individual['teacher_counts'][t_id] < self.max_shifts
                ]

                if eligible_teachers:
                    weights = []
                    for t_id in eligible_teachers:
                        stat = self.teacher_stats.get(t_id, {})
                        score = stat.get('agirlikli_puan', 1.0)
                        haftalik = stat.get('haftalik_ortalama', 1.0)
                        toplam = stat.get('toplam_nobet', 0)
                        # Adaletli ağırlık: az nöbet yapanın şansı artsın
                        w = (score + 1 / (haftalik + 1)) / (1 + toplam)
                        weights.append(max(w, 0.05))  # sıfır olmasın

                    new_teacher = random.choices(eligible_teachers, weights=weights, k=1)[0]
                    old_teacher = assignment['teacher_id']

                    individual['teacher_counts'][old_teacher] -= 1
                    individual['teacher_schedule'][old_teacher].discard(assignment['hour'])
                    assignment['teacher_id'] = new_teacher
                    individual['teacher_counts'][new_teacher] += 1
                    individual['teacher_schedule'][new_teacher].add(assignment['hour'])
        return individual

    # ======================================================
    # 🔹 Ceza hesaplama (adil ve yer bazlı)
    # ======================================================
    def calculate_penalty(self, solution):
        penalty = 0
        counts = list(solution['teacher_counts'].values())

        if counts:
            penalty += (max(counts) - min(counts)) * self.penalty_weights['inequality']

        penalty += (len(self.absent_classes) - len(solution['assignments'])) * self.penalty_weights['unassigned']
        penalty += len([t_id for t_id in self.teacher_ids if solution['teacher_counts'][t_id] == 0]) * self.penalty_weights['no_duty']

        # 🔸 Aşırı yüklenme
        overload = sum(max(0, c - self.max_shifts) for c in counts)
        penalty += overload * self.penalty_weights['overload']

        # 🔸 Çakışan saat
        conflicts = 0
        teacher_hours = defaultdict(set)
        for a in solution['assignments']:
            if a['hour'] in teacher_hours[a['teacher_id']]:
                conflicts += 1
            else:
                teacher_hours[a['teacher_id']].add(a['hour'])
        penalty += conflicts * self.penalty_weights['conflict']

        # 🔸 Adalet (istatistik farkı)
        fairness_penalty = 0
        for t_id, count in solution['teacher_counts'].items():
            stats = self.teacher_stats.get(t_id)
            if stats:
                haftalik = stats.get('haftalik_ortalama', 1.0)
                score = stats.get('agirlikli_puan', 1.0)
                ideal = 1 / (haftalik + 1)
                fairness_penalty += abs(count - ideal * self.max_shifts)
        penalty += fairness_penalty * self.penalty_weights['unfair']

        # 🔸 Aynı nöbet yerinde art arda görev cezası
        for a in solution['assignments']:
            tid = a['teacher_id']
            sinif_adi = a['class']
            stats = self.teacher_stats.get(tid)
            if stats and stats.get('son_nobet_yeri') == sinif_adi:
                penalty += self.penalty_weights['same_location']

        return penalty

    # ======================================================
    # 🔹 Yardımcı Fonksiyonlar
    # ======================================================
    def prepare_availability(self, teachers):
        availability = {}
        for t in teachers:
            tid = t['ogretmen_id']
            busy = set(t['dersleri'].keys())
            availability[tid] = {h: (h not in busy) for h in range(1, 9)}
        return availability

    def flatten_absent(self, absent_teachers):
        return [{'hour': int(h), 'class': c, 'absent_teacher_id': t['ogretmen_id']}
                for t in absent_teachers for h, c in t['dersleri'].items()]

    def format_solution(self, solution):
        assigned = {(a['hour'], a['class']) for a in solution['assignments']}
        all_classes = {(c['hour'], c['class']) for c in self.absent_classes}
        unassigned = [{'hour': c['hour'], 'class': c['class'], 'absent_teacher_id': c['absent_teacher_id']}
                      for c in self.absent_classes if (c['hour'], c['class']) not in assigned]

        return {
            'assignments': solution['assignments'],
            'unassigned': unassigned,
            'teacher_counts': dict(solution['teacher_counts']),
            'teacher_schedule': {k: list(v) for k, v in solution['teacher_schedule'].items()},
            'penalty': self.calculate_penalty(solution)
        }

    def create_individual(self):
        """
        Başlangıç bireyini üretir.
        - Uygun saatlerde, max_shifts sınırına uyarak
        - İstatistiklere göre (agirlikli_puan, haftalik_ortalama, toplam_nobet) ağırlıklı seçim yapar.
        """
        solution = {
            'assignments': [],
            'teacher_counts': defaultdict(int),
            'teacher_schedule': defaultdict(set),
        }
    
        for cls in self.absent_classes:
            hour = cls['hour']
            # Uygun öğretmenler
            eligible = [
                t_id for t_id in self.teacher_ids
                if self.availability[t_id][hour]
                and hour not in solution['teacher_schedule'][t_id]
                and solution['teacher_counts'][t_id] < self.max_shifts
            ]
    
            if not eligible:
                # Bu ders/saat şimdilik atanmıyor; format_solution unassigned'a düşürecek
                continue
    
            # Ağırlıklı seçim: az nöbet yapanın şansı artsın
            weights = []
            for t_id in eligible:
                stat = self.teacher_stats.get(t_id, {})
                score = float(stat.get('agirlikli_puan', 1.0))
                haftalik = float(stat.get('haftalik_ortalama', 1.0))
                toplam = int(stat.get('toplam_nobet', 0))
                # basit bir adalet heuristiği
                w = (score + 1.0 / (haftalik + 1.0)) / (1.0 + toplam)
                weights.append(max(w, 0.05))  # sıfıra yaklaşmasın
    
            chosen = random.choices(eligible, weights=weights, k=1)[0]
    
            solution['assignments'].append({
                'hour': hour,
                'class': cls['class'],
                'teacher_id': chosen,
                'absent_teacher_id': cls['absent_teacher_id'],
            })
            solution['teacher_counts'][chosen] += 1
            solution['teacher_schedule'][chosen].add(hour)
    
        return solution
