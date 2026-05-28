const { createApp } = Vue;

createApp({
    data() {
        return {
            currentUser: null,
            showExpertRequestModal: false,
            expertRequest: {
                description: '',
                location: '',
                observation_date: '',
                additional_data: ''
            },
            expertRequestError: '',
            expertRequestSuccess: '',
            submittingRequest: false,
            selectedType: null,
            loading: false,
            searchPerformed: false,
            viewingAll: false,
            results: [],
            allInsectsCount: 0,
            viewAllSearchQuery: '',
            viewAllTypeFilter: '',
            filteredViewAllResults: [],
            searchParams: {
                // Общие параметры
                sizeMin: null,
                sizeMax: null,
                color: '',
                habitat: '',
                season: '',
                // Для стрекоз
                bodyLengthMin: null,
                bodyLengthMax: null,
                wingspanMin: null,
                wingspanMax: null,
                eyeColor: '',
                environment: '',
                gender: '',
                // Для жуков
                surfaceType: '',
                elytra: '',
                // Для бабочек
                wingPattern: '',
                timeOfDay: '',
                // Грибы
                cap: '',
                stalk: '',
                growth: '',
                sizeCategory: '',
                // Травы
                lifeForm: '',
                leaf: '',
                aroma: '',
                flowerState: ''
            },
            insectTypes: [
                { value: 'dragonfly', label: 'Стрекоза', icon: '', image: '/static/images/dragon.png' },
                { value: 'beetle', label: 'Жук', icon: '🪲' },
                { value: 'butterfly', label: 'Бабочка', icon: '🦋' },
                { value: 'mushroom', label: 'Гриб', icon: '🍄' },
                { value: 'herb', label: 'Трава', icon: '🌿' }
            ],
            typeNames: {
                'dragonfly': { one: 'стрекоза', few: 'стрекозы', many: 'стрекоз' },
                'beetle': { one: 'жук', few: 'жука', many: 'жуков' },
                'butterfly': { one: 'бабочка', few: 'бабочки', many: 'бабочек' },
                'mushroom': { one: 'гриб', few: 'гриба', many: 'грибов' },
                'herb': { one: 'растение', few: 'растения', many: 'растений' }
            },
            catalogTypes: ['dragonfly', 'beetle', 'butterfly', 'mushroom', 'herb'],
            commonColors: ['синий', 'красный', 'зеленый', 'желтый', 'черный', 'коричневый', 'оранжевый', 'белый', 'фиолетовый', 'розовый'],
            commonHabitats: [
                { value: 'лес', label: 'Лес', icon: '' },
                { value: 'луг', label: 'Луг', icon: '' },
                { value: 'водоем', label: 'Водоем', icon: '' },
                { value: 'сад', label: 'Сад', icon: '' },
                { value: 'поле', label: 'Поле', icon: '' },
                { value: 'болото', label: 'Болото', icon: '' }
            ],
            seasons: [
                { value: 'весна', label: 'Весна', icon: '' },
                { value: 'лето', label: 'Лето', icon: '' },
                { value: 'осень', label: 'Осень', icon: '' },
                { value: 'зима', label: 'Зима', icon: '' }
            ],
            catalogFocusActive: false,
            catalogFocusError: '',
            filterOptions: {
                // Общие
                basicColors: [],
                colors: [],
                // Стрекозы
                basicEyeColors: [],
                eyeColors: [],
                basicHabitats: [],
                allHabitats: [],
                environments: [],
                seasons: [],
                // Жуки
                basicSurfaceTypes: [],
                allSurfaceTypes: [],
                basicElytra: [],
                allElytra: [],
                basicSeasons: [],
                allSeasons: [],
                // Бабочки
                basicWingPatterns: [],
                allWingPatterns: [],
                // Грибы
                basicSizeCategories: [],
                sizeCategories: [],
                allCaps: [],
                allStalks: [],
                // Травы
                basicLifeForms: [],
                lifeForms: [],
                basicDiscoveryPeriods: [],
                discoveryPeriods: [],
                basicFlowerStates: [],
                flowerStates: []
            }
        };
    },
    computed: {
        searchButtonLabel() {
            return this.loading ? 'Поиск...' : 'Найти';
        },
        canCreateExpertRequest() {
            return this.currentUser && this.currentUser.role === 'пользователь';
        },
        userRoleLabel() {
            if (!this.currentUser) return '';
            const labels = {
                'пользователь': 'Пользователь',
                'эксперт': 'Эксперт',
                'модератор': 'Модератор',
                'админ': 'Админ',
            };
            return labels[this.currentUser.role] || this.currentUser.role;
        },
    },
    methods: {
        openExpertRequestModal() {
            if (!this.canCreateExpertRequest) {
                return;
            }
            this.expertRequestError = '';
            this.expertRequestSuccess = '';
            this.showExpertRequestModal = true;
        },
        closeExpertRequestModal() {
            this.showExpertRequestModal = false;
        },
        async selectType(type) {
            this.selectedType = type;
            this.results = [];
            this.searchPerformed = false;
            this.viewingAll = false;
            
            // Загружаем опции фильтров из базы данных
            await this.loadFilterOptions(type);
        },
        
        async loadFilterOptions(type) {
            try {
                const response = await fetch(`/api/filter-options/${type}`);
                const data = await response.json();
                
                if (data.success && data.options) {
                    // Общие опции
                    this.filterOptions.basicColors = data.options.basic_colors || [];
                    this.filterOptions.colors = data.options.colors || [];
                    
                    // Стрекозы
                    if (type === 'dragonfly') {
                        this.filterOptions.basicEyeColors = data.options.basic_eye_colors || [];
                        this.filterOptions.eyeColors = data.options.eye_colors || [];
                        this.filterOptions.basicHabitats = data.options.basic_habitats || [];
                        this.filterOptions.allHabitats = data.options.all_habitats || data.options.habitats || [];
                        this.filterOptions.environments = data.options.environments || [];
                        this.filterOptions.seasons = data.options.seasons || [];
                    }
                    // Жуки
                    else if (type === 'beetle') {
                        this.filterOptions.basicSurfaceTypes = data.options.basic_surface_types || [];
                        this.filterOptions.allSurfaceTypes = data.options.all_surface_types || [];
                        this.filterOptions.basicElytra = data.options.basic_elytra || [];
                        this.filterOptions.allElytra = data.options.all_elytra || [];
                        this.filterOptions.basicHabitats = data.options.basic_habitats || [];
                        this.filterOptions.allHabitats = data.options.all_habitats || data.options.habitats || [];
                        this.filterOptions.basicSeasons = data.options.basic_seasons || [];
                        this.filterOptions.allSeasons = data.options.all_seasons || data.options.seasons || [];
                    }
                    // Бабочки
                    else if (type === 'butterfly') {
                        this.filterOptions.basicWingPatterns = data.options.basic_wing_patterns || [];
                        this.filterOptions.allWingPatterns = data.options.all_wing_patterns || [];
                        this.filterOptions.basicHabitats = data.options.basic_habitats || [];
                        this.filterOptions.allHabitats = data.options.all_habitats || data.options.habitats || [];
                        this.filterOptions.basicSeasons = data.options.basic_seasons || [];
                        this.filterOptions.allSeasons = data.options.all_seasons || data.options.seasons || [];
                    }
                    else if (type === 'mushroom') {
                        this.filterOptions.basicSizeCategories = data.options.basic_size_categories || [];
                        this.filterOptions.sizeCategories = data.options.size_categories || [];
                        this.filterOptions.basicHabitats = data.options.basic_habitats || [];
                        this.filterOptions.allHabitats = data.options.all_habitats || [];
                        this.filterOptions.basicSeasons = data.options.basic_seasons || [];
                        this.filterOptions.allSeasons = data.options.all_seasons || [];
                        this.filterOptions.allCaps = data.options.all_caps || [];
                        this.filterOptions.allStalks = data.options.all_stalks || [];
                    }
                    else if (type === 'herb') {
                        this.filterOptions.basicLifeForms = data.options.basic_life_forms || [];
                        this.filterOptions.lifeForms = data.options.life_forms || [];
                        this.filterOptions.basicColors = data.options.basic_colors || [];
                        this.filterOptions.colors = data.options.colors || [];
                        this.filterOptions.basicHabitats = data.options.basic_habitats || [];
                        this.filterOptions.allHabitats = data.options.all_habitats || [];
                        this.filterOptions.basicDiscoveryPeriods = data.options.basic_discovery_periods || [];
                        this.filterOptions.discoveryPeriods = data.options.discovery_periods || [];
                        this.filterOptions.basicFlowerStates = data.options.basic_flower_states || [];
                        this.filterOptions.flowerStates = data.options.flower_states || [];
                    }
                }
            } catch (error) {
                console.error('Ошибка при загрузке опций фильтров:', error);
            }
        },
        
        async showAllInsects() {
            this.loading = true;
            this.viewingAll = true;
            this.searchPerformed = false;
            this.selectedType = null;
            this.results = [];
            
            try {
                // Получаем все насекомые всех типов
                const types = this.catalogTypes;
                const allResults = [];
                
                for (const type of types) {
                    const response = await fetch(`/api/all/${type}`);
                    const data = await response.json();
                    
                    if (data.success && data.results) {
                        // Добавляем тип к каждому результату
                        const typedResults = data.results.map(insect => ({
                            ...insect,
                            insect_type: type
                        }));
                        allResults.push(...typedResults);
                    }
                }
                
                this.results = allResults;
                this.allInsectsCount = allResults.length;
                this.filteredViewAllResults = allResults;
            } catch (error) {
                alert('Ошибка при загрузке данных: ' + error.message);
                this.results = [];
                this.filteredViewAllResults = [];
            } finally {
                this.loading = false;
            }
        },
        
        filterViewAllResults() {
            if (!this.viewingAll || this.results.length === 0) {
                return;
            }
            
            let filtered = [...this.results];
            
            // Фильтр по типу
            if (this.viewAllTypeFilter) {
                filtered = filtered.filter(insect => insect.insect_type === this.viewAllTypeFilter);
            }
            
            // Фильтр по поисковому запросу
            if (this.viewAllSearchQuery.trim()) {
                const query = this.viewAllSearchQuery.toLowerCase().trim();
                filtered = filtered.filter(insect => {
                    const nameRu = (insect.name_ru || '').toLowerCase();
                    const nameLat = (insect.name_lat || '').toLowerCase();
                    const color = (insect.color || '').toLowerCase();
                    const habitat = (insect.habitat || '').toLowerCase();
                    const description = (insect.description || '').toLowerCase();
                    
                    return nameRu.includes(query) ||
                           nameLat.includes(query) ||
                           color.includes(query) ||
                           habitat.includes(query) ||
                           description.includes(query);
                });
            }
            
            this.filteredViewAllResults = filtered;
        },
        
        clearViewAllSearch() {
            this.viewAllSearchQuery = '';
            this.filterViewAllResults();
        },
        
        closeViewAll() {
            this.viewingAll = false;
            this.results = [];
            this.filteredViewAllResults = [];
            this.viewAllSearchQuery = '';
            this.viewAllTypeFilter = '';
            this.searchPerformed = false;
        },
        
        async searchInsects() {
            if (!this.selectedType) {
        alert('Пожалуйста, выберите категорию');
        return;
    }
    
            this.loading = true;
            this.searchPerformed = false;
            
            try {
                // Формируем параметры для запроса в зависимости от типа
    const params = {};
    
                if (this.selectedType === 'dragonfly') {
                    // Фильтры для стрекоз
                    if (this.searchParams.bodyLengthMin) {
                        params.body_length_min = this.searchParams.bodyLengthMin;
                    }
                    if (this.searchParams.bodyLengthMax) {
                        params.body_length_max = this.searchParams.bodyLengthMax;
                    }
                    if (this.searchParams.wingspanMin) {
                        params.wingspan_min = this.searchParams.wingspanMin;
                    }
                    if (this.searchParams.wingspanMax) {
                        params.wingspan_max = this.searchParams.wingspanMax;
                    }
                    if (this.searchParams.color.trim()) {
                        params.color = this.searchParams.color.trim();
                    }
                    if (this.searchParams.habitat.trim()) {
                        params.habitat = this.searchParams.habitat.trim();
                    }
                    if (this.searchParams.eyeColor.trim()) {
                        params.eye_color = this.searchParams.eyeColor.trim();
                    }
                    if (this.searchParams.environment.trim()) {
                        params.environment = this.searchParams.environment.trim();
                    }
                    if (this.searchParams.gender) {
                        params.gender = this.searchParams.gender;
                    }
                    if (this.searchParams.season) {
                        params.season = this.searchParams.season;
                    }
                } else if (this.selectedType === 'beetle') {
                    // Фильтры для жуков
                    if (this.searchParams.sizeMin) {
                        params.size_min = this.searchParams.sizeMin;
                    }
                    if (this.searchParams.sizeMax) {
                        params.size_max = this.searchParams.sizeMax;
                    }
                    if (this.searchParams.color.trim()) {
                        params.color = this.searchParams.color.trim();
                    }
                    if (this.searchParams.habitat.trim()) {
                        params.habitat = this.searchParams.habitat.trim();
                    }
                    if (this.searchParams.surfaceType.trim()) {
                        params.surface_type = this.searchParams.surfaceType.trim();
                    }
                    if (this.searchParams.elytra.trim()) {
                        params.elytra = this.searchParams.elytra.trim();
                    }
                    if (this.searchParams.season) {
                        params.season = this.searchParams.season;
                    }
                } else if (this.selectedType === 'butterfly') {
                    // Фильтры для бабочек
                    if (this.searchParams.sizeMin) {
                        params.size_min = this.searchParams.sizeMin;
                    }
                    if (this.searchParams.sizeMax) {
                        params.size_max = this.searchParams.sizeMax;
                    }
                    if (this.searchParams.color.trim()) {
                        params.color = this.searchParams.color.trim();
                    }
                    if (this.searchParams.wingPattern.trim()) {
                        params.wing_pattern = this.searchParams.wingPattern.trim();
                    }
                    if (this.searchParams.habitat.trim()) {
                        params.habitat = this.searchParams.habitat.trim();
                    }
                    if (this.searchParams.timeOfDay) {
                        params.time_of_day = this.searchParams.timeOfDay;
                    }
                    if (this.searchParams.season) {
                        params.season = this.searchParams.season;
                    }
                } else if (this.selectedType === 'mushroom') {
                    if (this.searchParams.habitat.trim()) {
                        params.habitat = this.searchParams.habitat.trim();
                    }
                    if (this.searchParams.season) {
                        params.season = this.searchParams.season;
                    }
                    if (this.searchParams.cap.trim()) {
                        params.cap = this.searchParams.cap.trim();
                    }
                    if (this.searchParams.stalk.trim()) {
                        params.stalk = this.searchParams.stalk.trim();
                    }
                    if (this.searchParams.growth.trim()) {
                        params.growth = this.searchParams.growth.trim();
                    }
                    if (this.searchParams.sizeCategory) {
                        params.size_category = this.searchParams.sizeCategory;
                    }
                } else if (this.selectedType === 'herb') {
                    if (this.searchParams.sizeMin) {
                        params.size_min = this.searchParams.sizeMin;
                    }
                    if (this.searchParams.sizeMax) {
                        params.size_max = this.searchParams.sizeMax;
                    }
                    if (this.searchParams.color.trim()) {
                        params.color = this.searchParams.color.trim();
                    }
                    if (this.searchParams.habitat.trim()) {
                        params.habitat = this.searchParams.habitat.trim();
                    }
                    if (this.searchParams.season) {
                        params.season = this.searchParams.season;
                    }
                    if (this.searchParams.lifeForm) {
                        params.life_form = this.searchParams.lifeForm;
                    }
                    if (this.searchParams.leaf.trim()) {
                        params.leaf = this.searchParams.leaf.trim();
                    }
                    if (this.searchParams.aroma.trim()) {
                        params.aroma = this.searchParams.aroma.trim();
                    }
                    if (this.searchParams.flowerState) {
                        params.flower_state = this.searchParams.flowerState;
                    }
                }
        
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                        type: this.selectedType,
                params: params
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
                    this.results = data.results || [];
                    this.searchPerformed = true;
        } else {
            alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                    this.results = [];
                    this.searchPerformed = true;
        }
    } catch (error) {
        alert('Ошибка при выполнении запроса: ' + error.message);
                this.results = [];
                this.searchPerformed = true;
            } finally {
                this.loading = false;
            }
        },
        
        clearForm() {
            this.searchParams = {
                sizeMin: null,
                sizeMax: null,
                color: '',
                habitat: '',
                season: '',
                bodyLengthMin: null,
                bodyLengthMax: null,
                wingspanMin: null,
                wingspanMax: null,
                eyeColor: '',
                environment: '',
                gender: '',
                surfaceType: '',
                elytra: '',
                wingPattern: '',
                timeOfDay: '',
                cap: '',
                stalk: '',
                growth: '',
                sizeCategory: '',
                lifeForm: '',
                leaf: '',
                aroma: '',
                flowerState: ''
            };
            this.results = [];
            this.searchPerformed = false;
            this.viewingAll = false;
        },
        
        formatSize(sizeMin, sizeMax) {
            const parts = [];
            if (sizeMin) parts.push(`${sizeMin} мм`);
            if (sizeMax) parts.push(`${sizeMax} мм`);
            return parts.join(' - ');
        },
        
        getTypeName(count) {
            if (!this.selectedType) return 'записей';
            
            const names = this.typeNames[this.selectedType];
            if (!names) return 'записей';
            
            // Простая логика для русского языка
            if (count === 0) return names.many;
            if (count === 1) return names.one;
            if (count >= 2 && count <= 4) return names.few;
            return names.many;
        },

        catalogRecordsLabel(count) {
            const n = Math.abs(Number(count) || 0);
            const mod10 = n % 10;
            const mod100 = n % 100;
            if (mod10 === 1 && mod100 !== 11) return 'запись';
            if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'записи';
            return 'записей';
        },

        habitatFieldLabel(type) {
            const labels = {
                mushroom: 'Место произрастания',
                herb: 'Место произрастания',
            };
            return labels[type] || 'Место обитания';
        },

        seasonFieldLabel(type) {
            const labels = {
                mushroom: 'Сезон',
                herb: 'Период обнаружения',
            };
            return labels[type] || 'Период';
        },

        colorFieldLabel(type) {
            const labels = {
                mushroom: 'Шляпка',
                herb: 'Цветок',
            };
            return labels[type] || 'Цвет';
        },
        
        toggleColor(color) {
            const current = this.searchParams.color.toLowerCase();
            if (current.includes(color.toLowerCase())) {
                // Убираем цвет
                this.searchParams.color = this.searchParams.color
                    .split(',')
                    .map(c => c.trim())
                    .filter(c => !c.toLowerCase().includes(color.toLowerCase()))
                    .join(', ')
                    .trim();
            } else {
                // Добавляем цвет
                if (this.searchParams.color) {
                    this.searchParams.color += ', ' + color;
                } else {
                    this.searchParams.color = color;
                }
            }
        },
        
        toggleHabitat(habitat) {
            const current = this.searchParams.habitat.toLowerCase();
            if (current.includes(habitat.toLowerCase())) {
                // Убираем место обитания
                this.searchParams.habitat = this.searchParams.habitat
                    .split(',')
                    .map(h => h.trim())
                    .filter(h => !h.toLowerCase().includes(habitat.toLowerCase()))
                    .join(', ')
                    .trim();
            } else {
                // Добавляем место обитания
                if (this.searchParams.habitat) {
                    this.searchParams.habitat += ', ' + habitat;
                } else {
                    this.searchParams.habitat = habitat;
                }
            }
        },
        
        selectQuickColor(color) {
            // Если цвет уже выбран, убираем его
            if (this.searchParams.color.toLowerCase().includes(color.toLowerCase())) {
                this.searchParams.color = '';
            } else {
                this.searchParams.color = color;
            }
        },
        
        selectQuickEyeColor(color) {
            // Если цвет уже выбран, убираем его
            if (this.searchParams.eyeColor.toLowerCase().includes(color.toLowerCase())) {
                this.searchParams.eyeColor = '';
            } else {
                this.searchParams.eyeColor = color;
            }
        },
        
        // Методы для базовых тегов жуков
        toggleBasicSurfaceType(type) {
            this.searchParams.surfaceType = this.searchParams.surfaceType === type ? '' : type;
        },
        
        toggleBasicElytra(elytra) {
            this.searchParams.elytra = this.searchParams.elytra === elytra ? '' : elytra;
        },
        
        // Методы для базовых тегов бабочек
        toggleBasicWingPattern(pattern) {
            this.searchParams.wingPattern = this.searchParams.wingPattern === pattern ? '' : pattern;
        },
        
        // Методы для базовых тегов мест нахождения (для всех типов)
        toggleBasicHabitat(habitat) {
            this.searchParams.habitat = this.searchParams.habitat === habitat ? '' : habitat;
        },
        
        // Методы для базовых тегов периодов (для жуков и бабочек)
        toggleBasicSeason(season) {
            this.searchParams.season = this.searchParams.season === season ? '' : season;
        },
        
        getTypeIcon(type) {
            return '';
        },
        
        isImageIcon(icon) {
            return typeof icon === 'string' && icon.startsWith('/static/');
        },
        
        toggleBasicFlowerState(state) {
            this.searchParams.flowerState = this.searchParams.flowerState === state ? '' : state;
        },

        toggleBasicDiscoveryPeriod(period) {
            this.searchParams.season = this.searchParams.season === period ? '' : period;
        },

        toggleBasicLifeForm(form) {
            this.searchParams.lifeForm = this.searchParams.lifeForm === form ? '' : form;
        },

        toggleBasicSizeCategory(size) {
            this.searchParams.sizeCategory = this.searchParams.sizeCategory === size ? '' : size;
        },

        getTypeLabel(type) {
            const labels = {
                'dragonfly': 'Стрекоза',
                'beetle': 'Жук',
                'butterfly': 'Бабочка',
                'mushroom': 'Гриб',
                'herb': 'Трава'
            };
            return labels[type] || 'Объект';
        },
        
        extractGender(description) {
            if (!description) return null;
            const desc = description.toLowerCase();
            if (desc.includes('пол: самец') || desc.includes('пол:самец')) {
                return 'самец';
            }
            if (desc.includes('пол: самка') || desc.includes('пол:самка')) {
                return 'самка';
            }
            if (desc.includes('самец/самка') || desc.includes('самец/самка')) {
                return 'самец/самка';
            }
            return null;
        },
        
        getGenderIcon(gender) {
            return '';
        },
        
        cleanDescription(description) {
            if (!description) return null;
            // Убираем информацию о поле из описания, так как она показывается отдельно
            return description
                .replace(/Пол:\s*(самец|самка|самец\/самка)[;,]?\s*/gi, '')
                .replace(/;\s*;/g, ';')
                .trim()
                .replace(/^;\s*/, '')
                .replace(/\s*;\s*$/, '');
        },
        
        async submitExpertRequest() {
            if (!this.canCreateExpertRequest) {
                this.expertRequestError = 'Создавать запросы эксперту могут только обычные пользователи';
                return;
            }
            if (!this.expertRequest.description.trim()) {
                this.expertRequestError = 'Описание насекомого обязательно';
                return;
            }
            
            this.submittingRequest = true;
            this.expertRequestError = '';
            this.expertRequestSuccess = '';
            
            try {
                const response = await fetch('/api/expert-request', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.expertRequest)
                });
                
                const data = await response.json();
                if (data.success) {
                    const id = data.request_id;
                    this.resetExpertRequest();
                    this.showExpertRequestModal = false;
                    if (id) {
                        window.location.href = `/request/${id}`;
                    }
                } else {
                    this.expertRequestError = data.error || 'Ошибка при отправке запроса';
                }
            } catch (error) {
                this.expertRequestError = 'Ошибка соединения с сервером';
            } finally {
                this.submittingRequest = false;
            }
        },
        
        resetExpertRequest() {
            this.expertRequest = {
                description: '',
                location: '',
                observation_date: '',
                additional_data: ''
            };
            this.expertRequestError = '';
            this.expertRequestSuccess = '';
        },
        
        async logout() {
            try {
                const response = await fetch('/logout', {
                    method: 'POST'
                });
                const data = await response.json();
                if (data.success) {
                    this.currentUser = null;
                    window.location.reload();
                }
            } catch (error) {
                console.error('Ошибка выхода:', error);
            }
        },

        initNotifications() {
            this.$nextTick(() => {
                if (window.UserNotifications && document.querySelector('#notifications-mount')) {
                    UserNotifications.init({ mount: '#notifications-mount' });
                }
            });
        },
        
        handleImageError(event) {
            // Скрываем изображение при ошибке загрузки
            if (event.target) {
                event.target.style.display = 'none';
                const container = event.target.closest('.insect-image-container');
                if (container) {
                    container.style.display = 'none';
                }
            }
        },

        catalogCardDomId(type, id) {
            if (!type || !id) return '';
            return `catalog-card-${type}-${id}`;
        },

        async openCatalogFromQuery() {
            const params = new URLSearchParams(window.location.search);
            const type = params.get('catalog');
            const id = parseInt(params.get('card_id') || params.get('id'), 10);
            if (!type || !id || !this.catalogTypes.includes(type)) {
                return;
            }
            window.location.replace(`/catalog/${type}/${id}`);
        },

        clearCatalogFocus() {
            this.catalogFocusActive = false;
            this.catalogFocusError = '';
            this.results = [];
            this.searchPerformed = false;
            this.selectedType = null;
            if (window.location.pathname.startsWith('/catalog/')) {
                window.history.replaceState({}, '', '/');
            }
        },

        async showCatalogCard(type, id) {
            this.catalogFocusError = '';
            this.loading = true;
            try {
                const response = await fetch(`/api/catalog/${type}/${id}`);
                const data = await response.json();
                if (!data.success || !data.insect) {
                    this.catalogFocusError = 'Карточка не найдена в каталоге.';
                    return;
                }
                const insect = { ...data.insect, insect_type: type };
                this.catalogFocusActive = true;
                this.selectedType = type;
                this.viewingAll = false;
                this.results = [insect];
                this.searchPerformed = true;
                await this.loadFilterOptions(type);
                await this.$nextTick();
                await this.$nextTick();
                const resultsSection = document.querySelector('.results-section');
                if (resultsSection) {
                    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                setTimeout(() => {
                    const el = document.getElementById(this.catalogCardDomId(type, id));
                    if (!el) return;
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    el.classList.add('catalog-card-highlight');
                    setTimeout(() => el.classList.remove('catalog-card-highlight'), 3500);
                }, 350);
            } catch (error) {
                console.error('Ошибка загрузки карточки каталога:', error);
                this.catalogFocusError = 'Не удалось загрузить карточку. Проверьте подключение к серверу.';
            } finally {
                this.loading = false;
            }
        },
    },
    mounted() {
        // Получаем данные пользователя из шаблона, если они переданы
        const userData = document.getElementById('user-data');
        if (userData) {
            try {
                this.currentUser = JSON.parse(userData.textContent);
            } catch (e) {
                this.currentUser = null;
            }
        }
        this.initNotifications();
        const deepLinkEl = document.getElementById('catalog-deep-link');
        if (deepLinkEl) {
            try {
                const link = JSON.parse(deepLinkEl.textContent);
                if (link && link.type && link.id) {
                    this.showCatalogCard(link.type, link.id);
                }
            } catch (e) {
                console.error('catalog deep link parse error', e);
            }
        } else {
            this.openCatalogFromQuery();
        }
    }
}).mount('#app');
