const { createApp } = Vue;

createApp({
  data() {
    return {
      publications: [],
      categories: [],
      selectedFilter: '*',
      loading: true,
      error: null
    }
  },
  computed: {
    filteredPublications() {
      if (this.selectedFilter === '*') {
        return this.publications;
      }
      return this.publications.filter(pub => 
        pub.filters.includes(this.selectedFilter.replace('.', ''))
      );
    }
  },
  async mounted() {
    await this.loadData();
  },
  methods: {
    async loadData() {
      try {
        this.loading = true;
        const response = await fetch('assets/data/publications.json');
        const data = await response.json();
        
        this.publications = data.publications;
        this.categories = data.categories;
        
        this.loading = false;
      } catch (error) {
        this.error = error.message;
        this.loading = false;
        console.error('加载publications数据时出错:', error);
      }
    },
    
    selectFilter(filter) {
      this.selectedFilter = filter;
      // 更新所有过滤器的active状态
      this.categories.forEach(cat => {
        cat.active = (cat.filter === filter);
      });
    }
  },
  template: `
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    
    <div v-else-if="error" class="alert alert-danger" role="alert">
      加载数据时出错: {{ error }}
    </div>
    
    <div v-else class="publications-container">
      <!-- Filters -->
      <ul class="portfolio-filters isotope-filters" data-aos="fade-up" data-aos-delay="100">
        <li 
          v-for="(category, index) in categories" 
          :key="category.filter"
          :data-filter="category.filter"
          :class="{ 'filter-active': category.active }"
          :style="{ 'animation-delay': (index * 0.1) + 's' }"
          class="filter-item"
          @click="selectFilter(category.filter)"
        >
          {{ category.name }}
        </li>
      </ul>
      
      <!-- Publications -->
      <div class="row gy-2 isotope-container">
        <div 
          v-for="(publication, index) in filteredPublications" 
          :key="publication.id"
          :class="['col-lg-12', 'isotope-item', ...publication.filters]"
          class="publication-item"
          :style="{ 'animation-delay': (index * 0.1) + 's' }"
        >
          <div class="publication-content">
            <h4>{{ publication.title }}</h4>
            <p class="authors">{{ publication.authors }}</p>
            <p class="venue">{{ publication.venue }}</p>
            <div class="publication-tags">
              <span 
                v-for="tag in publication.tags" 
                :key="tag" 
                class="tag"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
}).mount('#publications-app');
