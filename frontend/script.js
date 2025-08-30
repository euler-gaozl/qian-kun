document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://127.0.0.1:5001/api';

    // --- 通用函数 ---
    function generateContractList(productCode) {
        if (!productCode) return [];
        const contracts = [];
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        const yearSuffix = currentYear.toString().slice(-2);
        const nextYearSuffix = (currentYear + 1).toString().slice(-2);

        for (let month = currentMonth; month <= 12; month++) {
            contracts.push(`${productCode}${yearSuffix}${String(month).padStart(2, '0')}`);
        }
        for (let month = 1; month < currentMonth; month++) {
            contracts.push(`${productCode}${nextYearSuffix}${String(month).padStart(2, '0')}`);
        }
        return contracts;
    }

    function populateContractSelect(productCode, selectElement) {
        const contracts = generateContractList(productCode);
        selectElement.innerHTML = '';
        if (contracts.length > 0) {
            contracts.forEach(contract => {
                const option = document.createElement('option');
                option.value = contract;
                option.textContent = contract;
                selectElement.appendChild(option);
            });
        } else {
            selectElement.innerHTML = '<option value="">无可用合约</option>';
        }
    }

    // --- 实时策略模块 ---
    const strategyForm = document.getElementById('strategy-form');
    const strategyResult = document.getElementById('strategy-result');
    const strategyInstrumentSelect = document.getElementById('strategy-instrument');
    const strategyContractSelect = document.getElementById('strategy-contract');
    const strategyPeriodSelect = document.getElementById('strategy-period');

    strategyInstrumentSelect.addEventListener('change', (e) => {
        populateContractSelect(e.target.value, strategyContractSelect);
    });
    populateContractSelect(strategyInstrumentSelect.value, strategyContractSelect);

    strategyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const contract = strategyContractSelect.value;
        const period = strategyPeriodSelect.value;

        if (!contract) {
            strategyResult.innerHTML = `<p style="color: red;">请选择一个具体的合约。</p>`;
            return;
        }

        const data = { instrument: contract, period: period };
        strategyResult.innerHTML = '<p>正在执行策略...</p>';

        try {
            const response = await fetch(`${API_BASE_URL}/strategy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || `HTTP 错误! 状态: ${response.status}`);

            strategyResult.innerHTML = `
                <p><strong>合约:</strong> ${result.instrument}</p>
                <p><strong>周期:</strong> ${result.period}</p>
                <p><strong>操作:</strong> <span style="color: ${getActionColor(result.action)};">${result.action}</span></p>
                <p><strong>价格:</strong> ${result.price}</p>
                <p><strong>时间:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
            `;
        } catch (error) {
            strategyResult.innerHTML = `<p style="color: red;">执行失败: ${error.message}</p>`;
        }
    });

    // --- 策略回测模块 ---
    const backtestForm = document.getElementById('backtest-form');
    const backtestResult = document.getElementById('backtest-result');
    const backtestInstrumentSelect = document.getElementById('backtest-instrument');
    const backtestContractSelect = document.getElementById('backtest-contract');
    const backtestPeriodSelect = document.getElementById('backtest-period');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const initialCapitalInput = document.getElementById('initial-capital');

    const positionSizingPctInput = document.getElementById('position-sizing-pct');
    const useContinuousContractCheckbox = document.getElementById('use-continuous-contract');

    // 设置默认日期时间
    function setDefaultDateTime() {
        const now = new Date();
        const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate(), 9, 0); // 默认上午9点
        
        // 格式化为 YYYY-MM-DDTHH:mm
        const formatDateTimeLocal = (date) => {
            const pad = (num) => String(num).padStart(2, '0');
            return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
        };

        startDateInput.value = formatDateTimeLocal(oneYearAgo);
        endDateInput.value = formatDateTimeLocal(now);
    }
    setDefaultDateTime();

    backtestInstrumentSelect.addEventListener('change', (e) => {
        populateContractSelect(e.target.value, backtestContractSelect);
    });
    populateContractSelect(backtestInstrumentSelect.value, backtestContractSelect);

    useContinuousContractCheckbox.addEventListener('change', (e) => {
        backtestContractSelect.disabled = e.target.checked;
    });

    backtestForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const instrumentCode = backtestInstrumentSelect.value;
        const contract = backtestContractSelect.value;
        const useContinuous = useContinuousContractCheckbox.checked;

        if (!useContinuous && !contract) {
            backtestResult.innerHTML = `<p style="color: red;">请选择一个具体的合约，或勾选“使用加权合约”。</p>`;
            return;
        }

        const data = {
            instrument: useContinuous ? instrumentCode : contract,
            period: backtestPeriodSelect.value,
            start_date: startDateInput.value,
            end_date: endDateInput.value,
            initial_capital: parseFloat(initialCapitalInput.value),
            position_sizing_pct: parseFloat(positionSizingPctInput.value),
            use_continuous_contract: useContinuous
        };

        backtestResult.innerHTML = '<p>正在进行专业回测，请稍候...</p>';

        try {
            const response = await fetch(`${API_BASE_URL}/backtest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || `HTTP 错误! 状态: ${response.status}`);
            
            // --- 渲染新的专业回测报告 ---
            const kpis = result.kpis;
            const trades = result.trade_log;

            const kpiNameMap = {
                "yield_pct": "收益率",
                "win_rate": "胜率",
                "profit_loss_ratio": "盈亏比",
                "sharpe_ratio": "夏普比率",
                "max_drawdown": "最大回撤",
                "total_trades": "总交易次数"
            };

            let kpisHtml = '<h3>关键性能指标 (KPIs)</h3><table class="kpi-table">';
            for (const [key, value] of Object.entries(kpis)) {
                const displayName = kpiNameMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                kpisHtml += `<tr><td>${displayName}</td><td>${value}</td></tr>`;
            }
            kpisHtml += '</table>';

            let tradesHtml = '<h3>交易日志</h3>';
            if (trades && trades.length > 0) {
                tradesHtml += '<table class="trade-log-table"><thead><tr><th>入场时间</th><th>出场时间</th><th>方向</th><th>手数</th><th>入场均价</th><th>出场价</th><th>盈亏</th></tr></thead><tbody>';
                trades.forEach(trade => {
                    const profitLossColor = trade.profit_loss >= 0 ? 'green' : 'red';
                    // 确保显示为中文
                    const directionDisplay = trade.direction === 'long' ? '多' : (trade.direction === 'short' ? '空' : trade.direction);
                    tradesHtml += `
                        <tr>
                            <td>${new Date(trade.entry_time).toLocaleString()}</td>
                            <td>${new Date(trade.exit_time).toLocaleString()}</td>
                            <td>${directionDisplay}</td>
                            <td>${trade.lots}</td>
                            <td>${trade.entry_price.toFixed(2)}</td>
                            <td>${trade.exit_price.toFixed(2)}</td>
                            <td style="color: ${profitLossColor};">${trade.profit_loss.toFixed(2)}</td>
                        </tr>
                    `;
                });
                tradesHtml += '</tbody></table>';
            } else {
                tradesHtml += '<p>无交易记录。</p>';
            }

            backtestResult.innerHTML = kpisHtml + tradesHtml;

        } catch (error) {
            backtestResult.innerHTML = `<p style="color: red;">回测失败: ${error.message}</p>`;
        }
    });

    function getActionColor(action) {
        switch (action) {
            case '多开': return 'green';
            case '空开': return 'red';
            case '平仓': return 'orange';
            default: return 'gray';
        }
    }
});
