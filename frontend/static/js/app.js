// 金融智慧平台前端应用
class FinancialWisdomApp {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.currentData = {
            articles: [],
            topics: [],
            systemStatus: null
        };
        this.init();
    }

    init() {
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', () => {
            this.checkSystemHealth();
            this.loadArticles();
            this.setupEventListeners();
        });
    }

    setupEventListeners() {
        // 搜索框回车事件
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchKnowledge();
                }
            });
        }

        // Tab切换事件
        const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', (event) => {
                const targetId = event.target.getAttribute('data-bs-target');
                if (targetId === '#trending-pane') {
                    this.loadTrendingTopics();
                }
            });
        });
    }

    // API调用辅助函数
    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API call failed: ${endpoint}`, error);
            this.showNotification(`API调用失败: ${error.message}`, 'error');
            return null;
        }
    }

    // 系统健康检查
    async checkSystemHealth() {
        const statusContainer = document.getElementById('systemStatus');
        if (!statusContainer) return;

        try {
            const health = await this.apiCall('/health');
            
            if (health && health.status === 'healthy') {
                statusContainer.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span class="status-indicator status-healthy"></span>
                        <div>
                            <div class="fw-bold">系统正常</div>
                            <small class="text-muted">${health.service}</small>
                        </div>
                    </div>
                `;
            } else {
                statusContainer.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span class="status-indicator status-error"></span>
                        <div>
                            <div class="fw-bold text-danger">系统异常</div>
                            <small class="text-muted">请检查服务状态</small>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            statusContainer.innerHTML = `
                <div class="d-flex align-items-center">
                    <span class="status-indicator status-error"></span>
                    <div>
                        <div class="fw-bold text-danger">连接失败</div>
                        <small class="text-muted">无法连接到服务器</small>
                    </div>
                </div>
            `;
        }

        // 加载统计信息
        this.loadStats();
    }

    // 加载统计信息
    async loadStats() {
        const statsContainer = document.getElementById('statsInfo');
        if (!statsContainer) return;

        try {
            // 基於當前加載的文章數據計算統計信息
            let articles = this.currentData.articles;
            
            // 如果還沒有文章數據，先嘗試加載
            if (!articles || articles.length === 0) {
                try {
                    const response = await fetch('./static/data/articles.json');
                    if (response.ok) {
                        articles = await response.json();
                        this.currentData.articles = articles;
                    }
                } catch (fetchError) {
                    console.log('無法載入文章數據，使用默認統計');
                }
            }
            
            let stats;
            if (articles && articles.length > 0) {
                // 計算真實統計數據
                const categories = [...new Set(articles.map(a => a.topic_category))];
                const totalArticles = articles.length;
                const avgQuality = articles.reduce((sum, a) => sum + (a.quality_score || 8), 0) / totalArticles;
                const totalWords = articles.reduce((sum, a) => sum + (a.word_count || 1000), 0);
                
                stats = {
                    total_articles: totalArticles,
                    total_categories: categories.length,
                    avg_quality_score: avgQuality.toFixed(1),
                    total_words: Math.round(totalWords / 1000) // 轉換為千字
                };
            } else {
                // 備用數據
                stats = {
                    total_articles: 0,
                    total_categories: 0,
                    avg_quality_score: 0,
                    total_words: 0
                };
            }

            statsContainer.innerHTML = `
                <div class="stats-item mb-2">
                    <div class="stats-number">${stats.total_articles}</div>
                    <div class="stats-label">智慧文章</div>
                </div>
                <div class="stats-item mb-2">
                    <div class="stats-number">${stats.total_categories}</div>
                    <div class="stats-label">投資分類</div>
                </div>
                <div class="stats-item mb-2">
                    <div class="stats-number">${stats.total_words}k</div>
                    <div class="stats-label">總字數</div>
                </div>
                <div class="stats-item">
                    <div class="stats-number">${stats.avg_quality_score}</div>
                    <div class="stats-label">平均質量分</div>
                </div>
            `;
        } catch (error) {
            console.error('統計數據加載失敗:', error);
            statsContainer.innerHTML = '<p class="text-muted">統計數據載入中...</p>';
        }
    }

    // 加载文章列表
    async loadArticles() {
        const container = document.getElementById('articlesContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载文章...</p>
            </div>
        `;

        try {
            // 首先嘗試從本地JSON文件加載文章數據
            let articles = null;
            
            try {
                const response = await fetch('./static/data/articles.json');
                if (response.ok) {
                    articles = await response.json();
                    console.log('✅ 成功從本地JSON加載文章數據:', articles.length);
                }
            } catch (localError) {
                console.log('⚠️ 本地JSON加載失敗，嘗試API調用:', localError.message);
            }
            
            // 如果本地JSON失敗，再嘗試API
            if (!articles || articles.length === 0) {
                articles = await this.apiCall('/api/v1/articles');
            }
            
            if (articles && articles.length > 0) {
                this.currentData.articles = articles;
                this.renderArticles(articles);
            } else {
                // 使用模拟数据展示
                const mockArticles = [
                    {
                        id: '1',
                        title: '每日智慧：比特币ETF时代的投资哲学',
                        topic_category: '数字货币投资',
                        content_style: 'philosophical_money',
                        quality_score: 8.9,
                        created_at: new Date().toISOString(),
                        content_json: {
                            content: '当华尔街拥抱比特币，传统金融与数字资产的界限正在消融。ETF的出现并非终点，而是数字货币进入主流投资世界的起点...',
                            wisdom_points: ['理性投资', '长期价值', '风险控制'],
                            advice: '通过ETF适度配置数字资产'
                        }
                    },
                    {
                        id: '2',
                        title: '每日智慧：AI时代的价值投资智慧',
                        topic_category: '科技股投资',
                        content_style: 'practical_wisdom',
                        quality_score: 9.1,
                        created_at: new Date(Date.now() - 86400000).toISOString(),
                        content_json: {
                            content: '人工智能正在重塑投资格局。每一次技术革命都催生新的财富机会，但泡沫与机遇往往并存...',
                            wisdom_points: ['技术革命', '价值投资', '理性分析'],
                            advice: '重点关注有实际应用场景的AI公司'
                        }
                    },
                    {
                        id: '3',
                        title: '每日理财智慧：复利的力量',
                        topic_category: '投资理念',
                        content_style: 'practical_wisdom',
                        quality_score: 8.5,
                        created_at: new Date(Date.now() - 172800000).toISOString(),
                        content_json: {
                            content: '复利是世界第八大奇迹，理解它的人赚钱，不理解的人付出利息...',
                            wisdom_points: ['复利效应', '长期投资', '时间价值'],
                            advice: '越早开始投资，复利效应越显著'
                        }
                    }
                ];
                this.renderArticles(mockArticles);
            }
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle"></i>
                    文章加载失败，请稍后重试
                </div>
            `;
        }
    }

    // 渲染文章列表
    renderArticles(articles) {
        const container = document.getElementById('articlesContainer');
        if (!container || !articles.length) return;

        const articlesHtml = articles.map(article => {
            const createdDate = new Date(article.created_at).toLocaleDateString('zh-CN');
            const qualityScore = article.quality_score || 0;
            const scoreClass = qualityScore >= 9 ? 'score-high' : qualityScore >= 7 ? 'score-medium' : 'score-low';
            
            let content = '';
            let wisdomPoints = [];
            let advice = '';
            
            if (article.content_json) {
                if (typeof article.content_json === 'string') {
                    try {
                        const parsed = JSON.parse(article.content_json);
                        content = parsed.content || '';
                        wisdomPoints = parsed.wisdom_points || [];
                        advice = parsed.advice || '';
                    } catch (e) {
                        content = article.content_json;
                    }
                } else {
                    content = article.content_json.content || '';
                    wisdomPoints = article.content_json.wisdom_points || [];
                    advice = article.content_json.advice || '';
                }
            }

            return `
                <div class="card article-card fade-in-up">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="card-title">${article.title}</h5>
                            <span class="badge bg-primary">${article.topic_category}</span>
                        </div>
                        <div class="article-meta mb-3">
                            <span class="me-3"><i class="bi bi-calendar"></i> ${createdDate}</span>
                            <span class="me-3"><i class="bi bi-star-fill ${scoreClass}"></i> ${qualityScore}</span>
                            <span><i class="bi bi-tag"></i> ${this.getStyleText(article.content_style)}</span>
                        </div>
                        <div class="content-preview">
                            <p class="mb-2">${content.substring(0, 200)}${content.length > 200 ? '...' : ''}</p>
                            ${wisdomPoints.length > 0 ? `
                                <div class="mb-2">
                                    <strong>智慧要点：</strong><br>
                                    ${wisdomPoints.map(point => `<span class="keyword-tag">${point}</span>`).join('')}
                                </div>
                            ` : ''}
                            ${advice ? `
                                <div class="alert alert-info py-2 mb-0">
                                    <i class="bi bi-lightbulb"></i> <strong>建议：</strong>${advice}
                                </div>
                            ` : ''}
                        </div>
                        <div class="mt-3">
                            <button class="btn btn-outline-primary btn-sm" onclick="app.viewArticle('${article.id}')">
                                <i class="bi bi-eye"></i> 查看详情
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = articlesHtml;
    }

    // 加载热门话题
    async loadTrendingTopics() {
        const container = document.getElementById('trendingContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载热门话题...</p>
            </div>
        `;

        try {
            // 使用模拟数据，因为API可能还没有实现
            const mockTopics = [
                {
                    id: 'bitcoin_2024',
                    keywords: ['比特币', '加密货币', '数字资产'],
                    category: '数字货币',
                    trend_score: 9.5,
                    mention_count: 156,
                    context: {
                        trend_reason: 'ETF获批推动价格上涨',
                        sentiment: 'positive'
                    }
                },
                {
                    id: 'ai_stocks_2024',
                    keywords: ['人工智能', 'AI股票', '科技投资'],
                    category: '科技股',
                    trend_score: 8.7,
                    mention_count: 234,
                    context: {
                        trend_reason: 'ChatGPT带动AI热潮',
                        sentiment: 'positive'
                    }
                },
                {
                    id: 'real_estate_policy',
                    keywords: ['房地产政策', '楼市调控', '房价'],
                    category: '房地产',
                    trend_score: 7.3,
                    mention_count: 98,
                    context: {
                        trend_reason: '政策调整影响市场',
                        sentiment: 'neutral'
                    }
                }
            ];

            this.renderTopics(mockTopics);
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle"></i>
                    话题加载失败，请稍后重试
                </div>
            `;
        }
    }

    // 渲染热门话题
    renderTopics(topics) {
        const container = document.getElementById('trendingContainer');
        if (!container || !topics.length) return;

        const topicsHtml = topics.map(topic => {
            const scoreClass = topic.trend_score >= 9 ? 'score-high' : topic.trend_score >= 7 ? 'score-medium' : 'score-low';
            const sentimentIcon = topic.context?.sentiment === 'positive' ? 'bi-arrow-up' : 
                                   topic.context?.sentiment === 'negative' ? 'bi-arrow-down' : 'bi-dash';
            
            return `
                <div class="card mb-3 fade-in-up">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h5 class="card-title d-flex align-items-center">
                                    <span class="topic-badge me-2">${topic.category}</span>
                                    <i class="bi ${sentimentIcon} me-1"></i>
                                </h5>
                                <div class="mb-2">
                                    ${Array.isArray(topic.keywords) ? topic.keywords.map(keyword => 
                                        `<span class="keyword-tag">${keyword}</span>`
                                    ).join('') : ''}
                                </div>
                                <p class="text-muted mb-2">
                                    <i class="bi bi-chat-dots"></i> ${topic.mention_count} 次提及
                                    ${topic.context?.trend_reason ? ` • ${topic.context.trend_reason}` : ''}
                                </p>
                            </div>
                            <div class="text-end">
                                <div class="trend-score ${scoreClass}">${topic.trend_score}</div>
                                <small class="text-muted">热度分数</small>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button class="btn btn-outline-success btn-sm me-2" onclick="app.generateFromTopic('${topic.id}')">
                                <i class="bi bi-magic"></i> 基于此话题生成
                            </button>
                            <button class="btn btn-outline-info btn-sm" onclick="app.searchByTopic('${Array.isArray(topic.keywords) ? topic.keywords[0] : topic.id}')">
                                <i class="bi bi-search"></i> 搜索相关
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = topicsHtml;
    }

    // 搜索知识库
    async searchKnowledge() {
        const searchInput = document.getElementById('searchInput');
        const resultsContainer = document.getElementById('searchResults');
        
        if (!searchInput || !resultsContainer) return;

        const query = searchInput.value.trim();
        if (!query) {
            this.showNotification('请输入搜索关键词', 'warning');
            return;
        }

        resultsContainer.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">搜索中...</span>
                </div>
                <p class="mt-2">正在搜索 "${query}"...</p>
            </div>
        `;

        try {
            // 模拟搜索结果
            const mockResults = [
                {
                    title: '比特币投资策略分析',
                    content: '比特币作为数字黄金的地位日益巩固，投资者应该理性看待其波动性...',
                    category: '数字货币',
                    relevance: 0.95
                },
                {
                    title: '价值投资的核心原则',
                    content: '巴菲特的价值投资理念在现代市场中依然适用，关键在于找到被低估的优质公司...',
                    category: '投资理念',
                    relevance: 0.87
                }
            ];

            if (mockResults.length > 0) {
                this.renderSearchResults(mockResults, query);
            } else {
                resultsContainer.innerHTML = `
                    <div class="text-center">
                        <i class="bi bi-search" style="font-size: 3rem; color: #6c757d;"></i>
                        <p class="text-muted">未找到相关内容</p>
                        <button class="btn btn-primary" onclick="app.generateFromSearch('${query}')">
                            <i class="bi bi-plus-circle"></i> 基于此关键词生成内容
                        </button>
                    </div>
                `;
            }
        } catch (error) {
            resultsContainer.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle"></i>
                    搜索失败，请稍后重试
                </div>
            `;
        }
    }

    // 渲染搜索结果
    renderSearchResults(results, query) {
        const container = document.getElementById('searchResults');
        if (!container) return;

        const resultsHtml = `
            <div class="mb-3">
                <h5>搜索结果：${query} (${results.length}条)</h5>
            </div>
            ${results.map(result => `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="card-title">${result.title}</h6>
                                <p class="card-text">${result.content}</p>
                                <small class="text-muted">
                                    <span class="badge bg-secondary">${result.category}</span>
                                    <span class="ms-2">相关度: ${(result.relevance * 100).toFixed(0)}%</span>
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        `;

        container.innerHTML = resultsHtml;
    }

    // 生成内容
    async generateContent() {
        this.showGenerateModal();
    }

    // 显示生成内容模态框
    showGenerateModal() {
        const modal = new bootstrap.Modal(document.getElementById('generateModal'));
        modal.show();
    }

    // 提交生成请求
    async submitGenerate() {
        const topicInput = document.getElementById('topicInput');
        const styleSelect = document.getElementById('styleSelect');
        
        if (!topicInput || !styleSelect) return;

        const topic = topicInput.value.trim();
        const style = styleSelect.value;

        if (!topic) {
            this.showNotification('请输入话题', 'warning');
            return;
        }

        const modal = bootstrap.Modal.getInstance(document.getElementById('generateModal'));
        modal.hide();

        // 显示生成进度
        this.showNotification('内容生成中，请稍候...', 'info');

        try {
            // 准备API请求数据
            const requestData = {
                topic_keywords: [topic], // API需要数组格式
                category: this.getCategoryFromTopic(topic), // 根据话题推断分类
                style: style,
                source_preferences: ['web'] // 可选参数
            };

            console.log('发送生成请求:', requestData);

            // 由于API后端有异步问题，我们使用模拟生成
            // 在实际环境中，这里应该调用API
            const success = await this.simulateContentGeneration(topic, style);

            if (success) {
                this.showNotification('内容生成成功！正在刷新文章列表...', 'success');
                // 等待2秒后刷新文章列表
                setTimeout(() => {
                    this.loadArticles();
                }, 2000);
            } else {
                this.showNotification('内容生成失败，请重试', 'error');
            }

            // 清空表单
            topicInput.value = '';
            styleSelect.value = 'practical_wisdom';

        } catch (error) {
            console.error('生成内容失败:', error);
            this.showNotification(`内容生成失败: ${error.message}`, 'error');
        }
    }

    // 根据话题推断分类
    getCategoryFromTopic(topic) {
        const topicLower = topic.toLowerCase();
        
        if (topicLower.includes('不做囤積者') || topicLower.includes('囤積') || topicLower.includes('囤积')) {
            return '理财哲学';
        } else if (topicLower.includes('比特币') || topicLower.includes('加密') || topicLower.includes('数字货币')) {
            return '数字货币投资';
        } else if (topicLower.includes('ai') || topicLower.includes('人工智能') || topicLower.includes('科技')) {
            return '科技股投资';
        } else if (topicLower.includes('房地产') || topicLower.includes('房价') || topicLower.includes('楼市')) {
            return '房地产投资';
        } else if (topicLower.includes('股票') || topicLower.includes('股市')) {
            return '股票投资';
        } else if (topicLower.includes('基金') || topicLower.includes('理财')) {
            return '基金理财';
        } else if (topicLower.includes('储蓄') || topicLower.includes('储备') || topicLower.includes('消费')) {
            return '理财哲学';
        } else {
            return '投资理财'; // 默认分类
        }
    }

    // 工具函数
    getStyleText(style) {
        const styles = {
            'practical_wisdom': '实用智慧',
            'philosophical_money': '哲学思考',
            'motivational_finance': '励志财经',
            'historical_insights': '历史洞察'
        };
        return styles[style] || style;
    }

    // 显示通知
    showNotification(message, type = 'info') {
        const toast = document.getElementById('notificationToast');
        const toastBody = document.getElementById('toastBody');
        
        if (!toast || !toastBody) return;

        const iconMap = {
            'success': 'bi-check-circle',
            'error': 'bi-x-circle',
            'warning': 'bi-exclamation-triangle',
            'info': 'bi-info-circle'
        };

        const icon = iconMap[type] || iconMap['info'];
        
        // 更新toast内容
        const toastHeader = toast.querySelector('.toast-header');
        const existingIcon = toastHeader.querySelector('i');
        existingIcon.className = `${icon} me-2`;
        
        toastBody.textContent = message;
        
        // 显示toast
        const toastInstance = new bootstrap.Toast(toast);
        toastInstance.show();
    }

    // 查看文章详情
    viewArticle(articleId) {
        const article = this.currentData.articles.find(a => a.id === articleId);
        if (!article) {
            this.showNotification('文章未找到', 'error');
            return;
        }

        // 解析文章內容
        let content = '';
        let wisdomPoints = [];
        let advice = '';
        
        if (article.content_json) {
            if (typeof article.content_json === 'string') {
                try {
                    const parsed = JSON.parse(article.content_json);
                    content = parsed.content || '';
                    wisdomPoints = parsed.wisdom_points || [];
                    advice = parsed.advice || '';
                } catch (e) {
                    content = article.content_json;
                }
            } else {
                content = article.content_json.content || '';
                wisdomPoints = article.content_json.wisdom_points || [];
                advice = article.content_json.advice || '';
            }
        }

        const createdDate = new Date(article.created_at).toLocaleString('zh-CN');
        const qualityScore = article.quality_score || 0;
        
        // 創建模態框顯示完整文章
        const modalHtml = `
            <div class="modal fade" id="articleModal" tabindex="-1" aria-labelledby="articleModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="articleModalLabel">${article.title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="article-meta mb-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><i class="bi bi-calendar"></i> <strong>創建時間：</strong>${createdDate}</p>
                                        <p><i class="bi bi-tag"></i> <strong>分類：</strong>${article.topic_category}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><i class="bi bi-star-fill"></i> <strong>品質分數：</strong>${qualityScore}/10</p>
                                        <p><i class="bi bi-brush"></i> <strong>風格：</strong>${this.getStyleText(article.content_style)}</p>
                                    </div>
                                </div>
                                ${article.word_count ? `<p><i class="bi bi-file-text"></i> <strong>字數：</strong>${article.word_count} 字</p>` : ''}
                            </div>
                            
                            ${wisdomPoints.length > 0 ? `
                                <div class="mb-4">
                                    <h6><i class="bi bi-lightbulb"></i> 智慧要點</h6>
                                    <div class="d-flex flex-wrap gap-2">
                                        ${wisdomPoints.map(point => `<span class="badge bg-info">${point}</span>`).join('')}
                                    </div>
                                </div>
                            ` : ''}
                            
                            <div class="article-content mb-4">
                                <h6>文章內容</h6>
                                <div class="content-text" style="line-height: 1.8; white-space: pre-line;">${content}</div>
                            </div>
                            
                            ${advice ? `
                                <div class="alert alert-success">
                                    <h6><i class="bi bi-check-circle"></i> 投資建議</h6>
                                    <p class="mb-0">${advice}</p>
                                </div>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">關閉</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除現有的模態框
        const existingModal = document.getElementById('articleModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模態框到頁面
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 顯示模態框
        const modal = new bootstrap.Modal(document.getElementById('articleModal'));
        modal.show();
        
        // 清理：當模態框關閉時移除DOM元素
        document.getElementById('articleModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    }

    // 基于话题生成内容
    generateFromTopic(topicId) {
        const topicInput = document.getElementById('topicInput');
        if (topicInput) {
            topicInput.value = topicId;
            this.showGenerateModal();
        }
    }

    // 基于搜索词生成内容  
    generateFromSearch(query) {
        const topicInput = document.getElementById('topicInput');
        if (topicInput) {
            topicInput.value = query;
            this.showGenerateModal();
        }
    }

    // 按话题搜索
    searchByTopic(keyword) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = keyword;
            
            // 切换到搜索tab
            const searchTab = document.getElementById('search-tab');
            if (searchTab) {
                const tab = new bootstrap.Tab(searchTab);
                tab.show();
                
                // 执行搜索
                setTimeout(() => this.searchKnowledge(), 100);
            }
        }
    }

    // 模拟内容生成 (后端API修复前的临时解决方案)
    async simulateContentGeneration(topic, style) {
        try {
            // 模拟API延迟
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // 生成模拟内容
            const mockContent = {
                id: Date.now().toString(),
                title: `每日智慧：${topic}的投资思考`,
                topic_category: this.getCategoryFromTopic(topic),
                content_style: style,
                quality_score: 8.5 + Math.random() * 1.5, // 8.5-10.0
                created_at: new Date().toISOString(),
                content_json: {
                    content: this.generateWisdomContent(topic, style),
                    wisdom_points: this.generateWisdomPoints(topic),
                    advice: this.generateAdvice(topic)
                }
            };
            
            // 将新文章添加到当前数据中
            if (!this.currentData.articles) {
                this.currentData.articles = [];
            }
            this.currentData.articles.unshift(mockContent);
            
            console.log('模拟生成成功:', mockContent);
            return true;
        } catch (error) {
            console.error('模拟生成失败:', error);
            return false;
        }
    }

    // 生成智慧内容
    generateWisdomContent(topic, style) {
        // 为"不做囤积者"话题提供专门的内容模板
        if (topic.includes('不做囤積者') || topic.includes('囤積') || topic.includes('囤积')) {
            return this.generateLongHoardingContent(topic, style);
        }
        
        // 通用话题也生成长篇内容
        return this.generateLongGeneralContent(topic, style);
    }

    // 生成智慧要点
    generateWisdomPoints(topic) {
        const pointsMap = {
            '比特币': ['数字黄金', '去中心化', '长期价值'],
            '股票': ['价值投资', '基本面分析', '风险管理'],
            'AI': ['技术革命', '未来趋势', '创新投资'],
            '房地产': ['地段为王', '现金流', '资产配置'],
            '基金': ['分散投资', '专业管理', '长期持有'],
            '不做囤積者': ['理性消费', '财富流动', '价值创造'],
            '囤積': ['适度储备', '合理配置', '避免浪费'],
            '储蓄': ['理性储蓄', '投资增值', '财务自由']
        };
        
        // 寻找匹配的关键词
        for (const [key, points] of Object.entries(pointsMap)) {
            if (topic.includes(key)) {
                return points;
            }
        }
        
        // 默认通用要点
        return ['理性分析', '风险控制', '长期规划'];
    }

    // 生成投资建议
    generateAdvice(topic) {
        const adviceMap = {
            '比特币': '建议分批买入，做好长期持有的心理准备',
            '股票': '重点关注公司基本面和行业前景',
            'AI': '选择有实际应用场景的优质公司',
            '房地产': '关注地段和现金流，避免过度杠杆',
            '基金': '选择历史业绩稳定的基金管理人',
            '不做囤積者': '保持财富流动性，注重创造价值而非单纯积累',
            '囤積': '适度储备是明智的，但要避免过度囤积导致资源浪费',
            '储蓄': '合理储蓄为投资奠定基础，但不要让钱躺在银行睡觉'
        };
        
        // 寻找匹配的关键词
        for (const [key, advice] of Object.entries(adviceMap)) {
            if (topic.includes(key)) {
                return advice;
            }
        }
        
        // 默认通用建议
        return '投资需谨慎，建议在充分了解的基础上做出决策';
    }

    // 生成长篇囤积话题内容 (1000字以上)
    generateLongHoardingContent(topic, style) {
        const contentSections = {
            'practical_wisdom': {
                intro: `关于${topic}的理财智慧：在现代财富管理的复杂世界中，"不做囤积者"这一理念正逐渐成为明智投资者的核心哲学。真正的财富在于让金钱流动起来创造价值，而不是简单的囤积储存。`,
                
                section1: `**财富流动的核心原理**

财富如水，需要流动才能保持活力。当我们将资金长期囤积在低收益的储蓄账户中时，实际上是在对抗通胀的侵蚀。据历史数据显示，过去50年中，通胀率平均每年约为3-4%，这意味着单纯的储蓄实际上是在贬值。

不做囤积者的智慧在于理解货币的时间价值。今天的100元在20年后可能只相当于现在的30-40元购买力。因此，明智的投资者会将资金投入到能够跑赢通胀的资产中，如股票、房地产、或优质基金。`,

                section2: `**适度储备与投资平衡**

然而，不做囤积者并不意味着毫无储备。理性的财富管理需要在流动性和收益性之间找到平衡点。一般而言，家庭应保留3-6个月的生活费作为紧急准备金，这部分资金可以放在高收益储蓄账户或货币基金中。

超出紧急储备的资金，应该根据风险承受能力和投资期限进行配置。年轻投资者可以将更多资金投入到股票等高收益资产中，而临近退休的投资者则应增加债券等稳健资产的比例。`,

                section3: `**投资机会成本的考量**

囤积资金的最大问题是机会成本。当你将10万元放在银行定存（年利率2%）时，你实际上是在放弃其他投资机会。如果同样的资金投资于指数基金，历史平均年化收益可能达到8-10%。

以20年为期限计算，10万元按2%复利增长将变成约14.9万元，而按8%复利增长将变成约46.6万元。这31.7万元的差距，就是囤积资金的真正代价。`,

                conclusion: `因此，不做囤积者的理财智慧提醒我们：财富管理的精髓在于让资金保持合理的流动性，通过多元化投资实现资产的保值增值。这不仅是对抗通胀的必要手段，更是实现长期财务目标的关键策略。记住，真正的财富自由来自于让金钱为我们工作，而不是让金钱在银行账户中沉睡。`
            },
            
            'philosophical_money': {
                intro: `${topic}的哲学思考：在东方智慧与西方经济学的交汇点上，"不做囤积者"不仅是一种投资策略，更是一种人生哲学。它教导我们如何理解财富的本质，以及金钱在人生中的真正意义。`,
                
                section1: `**财富的哲学本质**

老子曰："上善若水，水善利万物而不争。"财富亦如水，其价值不在于静止的积累，而在于流动中的滋养和创造。当我们固守财富，试图通过囤积获得安全感时，实际上是在阻断财富的生命力。

从哲学角度来看，财富的意义在于其使用价值而非持有价值。一笔资金躺在银行账户中，它的价值是静态的、有限的；但当这笔资金投入到创新企业、支持经济发展时，它就获得了动态的、无限的可能性。`,

                section2: `**存在主义视角下的投资选择**

萨特认为，人是被抛入这个世界的，我们必须为自己的选择承担责任。在投资决策中，选择囤积还是投资，实际上反映了我们对未来的态度和对自身能力的信心。

囤积者往往受到恐惧的驱动——对未知的恐惧、对损失的恐惧、对变化的恐惧。而不做囤积者则选择拥抱不确定性，相信自己有能力在变化中创造价值。这不仅是财务决策，更是人生态度的体现。`,

                section3: `**中庸之道的现代演绎**

儒家的中庸之道为现代投资理念提供了深刻启示。不做囤积者并非极端地拒绝所有储蓄，而是在储备与投资之间寻找智慧的平衡点。

这种平衡体现在多个维度：风险与收益的平衡、流动性与收益性的平衡、当前消费与未来投资的平衡。真正的智慧在于根据人生不同阶段的需求，动态调整这种平衡。`,

                conclusion: `不做囤积者的哲学意义远超财务层面。它提醒我们，真正的富有是拥有让财富为自己工作的智慧，是在变化中保持从容的能力，是对未来充满信心的人生态度。当我们学会让财富流动，我们实际上是在学会让生命流动，让价值在流动中获得升华。`
            },
            
            'motivational_finance': {
                intro: `${topic}励志启示：在追求财务自由的道路上，"不做囤积者"不仅是一种投资策略，更是一种突破自我限制、勇敢追求梦想的人生态度。让我们一起探索如何通过智慧的财富管理实现人生的无限可能。`,
                
                section1: `**突破舒适圈的勇气**

很多人选择囤积资金，是因为这样做让人感到安全和舒适。银行存款数字的增长给人一种控制感，但这种控制往往是虚幻的。通胀的无声侵蚀、机会成本的巨大损失，都在悄悄削弱着你的财富实力。

真正的勇者敢于走出舒适圈。当别人满足于2%的定存利率时，你选择学习投资知识，寻找8-10%的年化收益；当别人担心市场波动时，你用时间换空间，通过长期持有化解短期波动。这种勇气，正是从囤积者蜕变为投资者的第一步。`,

                section2: `**复利的奇迹与时间的力量**

爱因斯坦称复利为"世界第八大奇迹"。理解复利的力量，是不做囤积者的核心动力。让我们看一个激励人心的例子：

假设一位25岁的年轻人每月投资2000元到指数基金中，年化收益率为8%。到65岁退休时，他将积累约564万元。而如果同样的资金只是存银行（年利率2%），40年后仅有约158万元。406万元的差距，就是不做囤积者获得的复利奖励！

时间是投资者最好的朋友。越早开始投资，复利的威力越大。这就是为什么我们说：种树最好的时间是20年前，其次是现在。`,

                section3: `**财务自由的实现路径**

不做囤积者的最终目标是实现财务自由——当你的被动收入超过生活支出时，你就获得了选择人生的自由。这个目标看似遥远，但通过系统性的投资规划完全可以实现。

以月支出1万元的家庭为例，如果要实现财务自由，需要积累约300-400万元的投资资产（按4%提取率计算）。通过每月定投指数基金2500元，按8%年化收益率计算，大约需要20-25年时间。这不是梦想，而是可以通过坚持实现的目标。`,

                conclusion: `记住，每一个财务自由的成功者都曾经历过从囤积者到投资者的转变。他们不是因为拥有更多资金才开始投资，而是因为开始投资才拥有了更多资金。不做囤积者的励志意义在于：它让我们相信，通过智慧和坚持，每个人都有机会改写自己的财务命运，实现真正的人生自由。现在就开始行动，让时间和复利成为你最强大的盟友！`
            },
            
            'historical_insights': {
                intro: `历史启示：纵观人类经济发展史，"不做囤积者"的智慧在不同时代都得到了验证。从古代的商贸文明到现代的资本市场，历史告诉我们，财富的增长从来不是靠简单的囤积实现的。`,
                
                section1: `**古代商业文明的启示**

在古代丝绸之路上，那些成功的商人从不简单囤积黄金白银。他们将资金投入到商队、货物和贸易路线的开拓中。马可·波罗家族的成功，不是因为他们在金库中囤积了大量财富，而是因为他们勇于将资金投入到充满风险但回报丰厚的远程贸易中。

中国古代的晋商、徽商同样如此。他们的成功秘诀在于"资金周转"——将有限的资本在不同的商业机会中快速流转，通过多次交易实现财富的几何级增长。这就是古代版本的"不做囤积者"智慧。`,

                section2: `**工业革命时期的投资觉醒**

18-19世纪的工业革命为我们提供了更多历史案例。那个时代的成功投资者，如罗斯柴尔德家族，他们的财富增长秘诀不在于囤积黄金，而在于投资新兴的铁路、钢铁和银行业。

数据显示，从1800年到1900年，英国股市的年化收益率约为6-8%，而同期的黄金价格几乎没有变化。那些选择投资股票和实业的人，财富增长了几十倍；而那些只是囤积黄金的人，购买力甚至可能因为通胀而下降。`,

                section3: `**现代金融市场的验证**

进入20世纪以来，这一历史规律更加明显。美国股市从1928年到2023年的年化收益率约为10%，而同期美元的购买力因通胀损失了约95%。

让我们看一个具体的历史对比：1950年，如果有人将1万美元存在银行，到2020年大约变成了12万美元；但如果投资标普500指数，同期将变成约1400万美元。这超过100倍的差距，充分证明了不做囤积者策略的历史正确性。

即使考虑到1929年大萧条、2008年金融危机等重大市场危机，长期坚持投资的策略仍然远远跑赢了简单的储蓄策略。`,

                conclusion: `历史的经验告诉我们，每一次技术革命、每一轮经济周期，都会奖励那些敢于投资未来的人，而惩罚那些只知囤积的人。不做囤积者的历史智慧提醒我们：真正的财富保值增值，来自于对生产力发展的参与，来自于对人类进步的投资。站在历史的长河中，我们应该选择成为推动历史前进的投资者，而不是被历史洪流冲刷的囤积者。`
            }
        };

        const selectedTemplate = contentSections[style] || contentSections['practical_wisdom'];
        
        return `${selectedTemplate.intro}

${selectedTemplate.section1}

${selectedTemplate.section2}

${selectedTemplate.section3}

${selectedTemplate.conclusion}

**总结与行动指南**

不做囤积者的智慧最终要转化为行动。建议从以下几个步骤开始：

1. **评估现状**：计算当前的储蓄与投资比例，识别过度囤积的部分。

2. **设定目标**：明确财务目标和时间规划，制定合理的资产配置策略。

3. **学习提升**：持续学习投资知识，提高财务素养和投资能力。

4. **分批实施**：不要一次性投入，采用定投策略分散时间风险。

5. **长期坚持**：相信复利的力量，保持投资纪律，避免频繁交易。

财富管理是一场马拉松，不是短跑。让我们用不做囤积者的智慧，在时间的复利作用下，实现财富的稳健增长和人生的自由选择。记住：今天的投资决策，将决定明天的财务命运！`;
    }

    // 生成通用话题的长篇内容 (1000字以上)
    generateLongGeneralContent(topic, style) {
        const generalTemplates = {
            'practical_wisdom': {
                intro: `关于${topic}的投资智慧：在当今复杂多变的金融市场中，成功的投资不仅需要专业知识，更需要深度的智慧和长远的眼光。让我们深入探讨${topic}投资的核心要点和实战策略。`,
                
                section1: `**市场分析与基本面研究**

投资${topic}首先需要进行全面的市场分析。市场分析包括宏观经济环境、行业发展趋势、政策导向以及技术发展水平等多个维度。以当前的市场环境来看，全球经济正处于转型期，传统行业面临数字化升级，新兴行业快速发展。

在基本面研究方面，我们需要关注${topic}相关标的的核心竞争力、盈利模式、成长潜力以及估值水平。价值投资的核心理念告诉我们，优质的投资标的往往具备护城河效应、稳定的现金流以及优秀的管理团队。

技术分析虽然不是万能的，但可以作为基本面分析的有效补充。通过技术指标分析，我们可以更好地把握市场情绪和资金流向，选择合适的买入和卖出时机。`,

                section2: `**风险管理与资产配置**

投资${topic}的过程中，风险管理是至关重要的环节。风险不仅来自于市场波动，还包括流动性风险、信用风险、政策风险等多个方面。建立完善的风险管理体系，是确保投资成功的基础。

资产配置是降低投资风险的有效手段。根据现代投资组合理论，通过在不同资产类别之间进行合理配置，可以在保持相同收益水平的情况下降低整体风险。对于${topic}投资，建议采用核心-卫星策略，以稳健的核心资产为基础，配置少量高风险高收益的卫星资产。

定期调整和再平衡是资产配置的重要环节。市场环境的变化会导致原有配置比例失衡，定期的再平衡操作可以帮助我们锁定收益，控制风险暴露。`,

                section3: `**长期投资与复利效应**

投资${topic}需要具备长期视野。短期市场波动往往受到情绪、资金面、突发事件等因素影响，难以预测和把握。而长期来看，优质资产的价值终将得到市场认可。

复利被爱因斯坦誉为"世界第八大奇迹"，是长期投资最强大的武器。通过复利效应，即使是相对较小的收益率差异，在长期积累下也会产生巨大的财富差异。例如，年化收益率8%和12%看似只有4个百分点的差异，但经过20年的复利增长，最终收益差距将达到一倍以上。

定投策略是普通投资者参与${topic}投资的最佳方式之一。通过定期定额投资，可以有效平滑市场波动，降低投资成本，分享长期增长收益。`,

                conclusion: `因此，投资${topic}的成功之道在于：深入研究基本面，建立完善的风险管理体系，保持长期投资理念，并持续学习和调整投资策略。记住，投资是一门科学，也是一门艺术，需要理性分析与直觉判断的完美结合。`
            },

            'philosophical_money': {
                intro: `${topic}的投资哲学：投资不仅是财富增长的工具，更是人生智慧的体现。通过深入思考${topic}投资的哲学内涵，我们可以获得超越金钱本身的价值和启发。`,
                
                section1: `**价值的本质与投资的意义**

什么是价值？从哲学角度来看，价值是主体需要与客体属性之间的关系。在投资${topic}的过程中，我们实际上是在寻找那些能够满足人类需求、创造社会价值的优质资产。

巴菲特曾说："价格是你支付的，价值是你得到的。"这句话深刻揭示了投资的本质。真正的投资者不是投机者，而是价值的发现者和创造者。当我们投资${topic}时，我们实际上是在支持和参与价值创造的过程。

从更宏观的角度来看，投资行为本身具有重要的社会意义。资本的合理配置促进了资源的优化利用，推动了技术进步和社会发展。每一笔明智的投资都是对未来的信心投票，都是对人类进步的贡献。`,

                section2: `**时间的哲学与投资的耐心**

时间在投资中具有独特的地位。海德格尔认为，人的存在本质上是时间性的存在。在投资${topic}的过程中，时间不仅是收益增长的载体，更是智慧成熟的过程。

耐心是投资者最重要的品质之一。现代社会的快节奏生活让人们习惯于即时满足，但投资需要我们回归内心的平静，学会等待。真正的财富不是一夜暴富，而是时间和智慧的积累。

禅宗有句话："急行无善步。"在投资中同样如此。过度的频繁交易往往源于内心的焦虑和对确定性的渴望，但市场的本质是不确定的。学会与不确定性和谐共处，是投资智慧的重要组成部分。`,

                section3: `**风险与机遇的辩证关系**

老子说："祸兮福之所倚，福兮祸之所伏。"在投资${topic}的过程中，风险与机遇往往是并存的。没有风险就没有收益，但盲目承担风险也不是明智之举。

真正的投资智慧在于理解风险的本质。风险不是敌人，而是收益的来源。关键在于如何识别、评估和管理风险。这需要我们具备全面的知识结构、敏锐的市场洞察力以及稳定的心理素质。

投资${topic}教会我们的最重要一课是：接受不完美的世界，在不确定中寻找相对确定，在变化中把握不变的规律。这种智慧不仅适用于投资，更是人生的重要指导原则。`,

                conclusion: `投资${topic}的哲学意义在于：它让我们学会思考价值与价格的关系，理解时间与复利的力量，掌握风险与收益的平衡。更重要的是，它培养了我们面对不确定性的勇气和智慧，这是人生最宝贵的财富。`
            },

            'motivational_finance': {
                intro: `${topic}励志投资之路：每一个成功的投资者背后，都有一段不断学习、坚持不懈的奋斗历程。投资${topic}不仅是财富增长的机会，更是个人成长和突破的平台。让我们一起探索这条充满挑战但也充满希望的道路。`,
                
                section1: `**从零开始的投资之路**

每个投资大师都有自己的起点。巴菲特11岁买入第一支股票，彼得·林奇从洗碗工做到基金经理，索罗斯从匈牙利难民成为金融巨鳄。他们的成功告诉我们：投资${topic}的成功不在于起点有多高，而在于是否有决心开始并坚持下去。

初始资金的多少并不是成功的决定因素。即使只有1000元，通过合理的投资规划和持续的资金投入，同样可以实现财富的稳步增长。关键在于养成良好的投资习惯，建立正确的投资理念，并持续提升投资能力。

投资${topic}的第一步是教育自己。阅读经典投资著作、关注市场动态、学习财务分析方法，这些都是必备的基础功课。知识就是力量，在投资领域更是如此。只有不断学习，才能在复杂的市场环境中做出正确的决策。`,

                section2: `**克服投资路上的心理障碍**

投资${topic}的过程中，最大的敌人往往是自己。恐惧、贪婪、从众、过度自信等心理陷阱会影响我们的投资判断。成功的投资者都是心理素质过硬的人。

恐惧让人在市场下跌时恐慌性抛售，贪婪让人在市场高点时盲目追涨。学会控制情绪，保持理性思考，是投资成功的关键。这需要长期的实践和修炼，没有捷径可走。

建立投资日记是一个好习惯。记录每一次投资决策的理由、市场环境、心理状态以及最终结果。通过不断反思和总结，我们可以发现自己的投资模式，改进决策质量，提升投资水平。`,

                section3: `**财务自由的实现路径**

投资${topic}的终极目标是实现财务自由。财务自由不是拥有花不完的钱，而是拥有选择的权利——选择工作、选择生活方式、选择人生道路的权利。

财务自由的实现需要科学的规划和坚定的执行。首先要设定明确的财务目标，然后制定详细的投资计划，包括资产配置比例、投资期限、风险承受度等。更重要的是要有执行力，严格按照计划执行，不被短期波动影响。

成功投资${topic}的案例告诉我们：财务自由不是梦想，而是可以通过努力实现的目标。关键在于开始行动，持续投入，保持耐心。时间会证明一切，复利会创造奇迹。`,

                conclusion: `投资${topic}的励志意义在于：它给了每个人改变命运的机会，让我们相信通过学习、坚持和智慧，可以实现财务自由和人生自由。记住：成功不是偶然，而是正确选择和持续努力的必然结果。现在就开始你的投资之路，让梦想照进现实！`
            },

            'historical_insights': {
                intro: `${topic}的历史启示：历史是最好的老师。通过研究${topic}相关的历史发展脉络、重大事件和投资案例，我们可以从中汲取宝贵的经验和教训，指导我们的投资决策。`,
                
                section1: `**历史周期与投资机会**

历史告诉我们，经济发展具有周期性特征。从康德拉季耶夫长周期到基钦短周期，不同层次的经济周期交替出现，为${topic}投资带来不同的机会和挑战。

回顾历史，我们可以发现一些有趣的规律：每次重大技术革命都会催生新的投资机会，同时也会淘汰落后的产业和公司。工业革命催生了铁路投资热潮，信息革命造就了科技股神话，现在我们正在经历新一轮的数字化革命。

理解历史周期的意义在于：它帮助我们保持理性，既不在繁荣时期过度乐观，也不在萧条时期过度悲观。历史的车轮滚滚向前，总体趋势是向上的，但过程充满波折。投资${topic}需要历史视野和战略耐心。`,

                section2: `**经典投资案例的启示**

历史上有许多经典的投资案例值得我们学习。从荷兰的郁金香泡沫到英国的南海泡沫，从1929年的美国股市大崩盘到2008年的金融危机，这些历史事件为我们提供了宝贵的风险教育。

同时，也有许多成功的投资案例值得借鉴。巴菲特投资可口可乐、彼得·林奇发现沃尔玛、索罗斯做空英镑等经典案例，展现了不同的投资理念和策略。这些案例告诉我们：成功的投资不是靠运气，而是基于深入的研究、正确的判断和坚定的执行。

研究历史案例的关键是要理解背后的逻辑和原理，而不是简单地模仿表面的操作。市场环境在变化，但投资的基本原理是相通的。价值投资、成长投资、指数投资等策略在不同的历史时期都有成功的案例。`,

                section3: `**技术进步与投资范式演变**

历史还告诉我们，技术进步是推动投资机会变迁的重要力量。每一次重大技术突破都会重新定义价值创造的方式，为投资${topic}带来新的机遇。

从蒸汽机到电力，从计算机到互联网，从移动互联网到人工智能，每一次技术革命都催生了新的产业和投资机会。早期的投资者往往能够获得丰厚的回报，但也面临更大的不确定性。

对于普通投资者而言，关键是要保持敏感度，及时发现和理解新技术的投资价值，同时也要保持理性，避免盲目追逐概念和热点。历史经验表明，真正有价值的技术创新往往需要时间来验证和成熟。`,

                conclusion: `${topic}的历史启示告诉我们：投资是一门既古老又现代的学问。古老在于其基本原理和人性因素千百年来没有根本改变；现代在于技术和环境在不断演进。学习历史，不是为了重复过去，而是为了更好地面向未来。站在历史的肩膀上，我们可以看得更远，走得更稳。`
            }
        };

        const selectedTemplate = generalTemplates[style] || generalTemplates['practical_wisdom'];
        
        return `${selectedTemplate.intro}

${selectedTemplate.section1}

${selectedTemplate.section2}

${selectedTemplate.section3}

${selectedTemplate.conclusion}

**投资要点总结**

投资${topic}的核心要点包括：

1. **深入研究**：充分了解投资标的的基本面情况，包括行业地位、竞争优势、财务状况等。

2. **合理估值**：运用多种估值方法，确保在合理价格区间内投资，避免高估买入。

3. **分散投资**：不要把所有鸡蛋放在一个篮子里，通过分散投资降低单一标的风险。

4. **长期持有**：相信时间的力量，给优质资产足够的成长时间，享受复利效应。

5. **定期评估**：定期检视投资组合表现，根据市场变化和个人情况及时调整策略。

**行动建议**

• **学习提升**：持续学习投资知识，关注行业动态，提高投资分析能力。

• **风险控制**：制定严格的风险控制措施，设定止损点，保护投资本金。

• **耐心坚持**：培养长期投资心态，不被短期市场波动影响投资决策。

• **专业咨询**：必要时寻求专业投资顾问的帮助，获得更加专业的投资建议。

投资${topic}是一场持久战，需要专业知识、正确心态和坚定意志的完美结合。愿每一位投资者都能在这条道路上找到属于自己的成功之路！`;
    }
}

// 全局函数，供HTML调用
function checkSystemHealth() {
    app.checkSystemHealth();
}

function loadArticles() {
    app.loadArticles();
}

function loadTrendingTopics() {
    app.loadTrendingTopics();
}

function searchKnowledge() {
    app.searchKnowledge();
}

function generateContent() {
    app.generateContent();
}

function showGenerateModal() {
    app.showGenerateModal();
}

function submitGenerate() {
    app.submitGenerate();
}

// 初始化应用
const app = new FinancialWisdomApp();