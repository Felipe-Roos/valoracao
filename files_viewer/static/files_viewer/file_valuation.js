(function () {
    'use strict';

    var config = window.VALUATION_CONFIG;
    var catalogEl = document.getElementById('valuation-catalog-data');
    var catalog = catalogEl ? JSON.parse(catalogEl.textContent) : [];

    function formatBRL(value) {
        return Number(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function findProduct(id) {
        for (var i = 0; i < catalog.length; i++) {
            for (var j = 0; j < catalog[i].products.length; j++) {
                if (String(catalog[i].products[j].id) === String(id)) return catalog[i].products[j];
            }
        }
        return null;
    }

    function createFieldRow(labelText, inputEl) {
        var row = document.createElement('div');
        row.className = 'field-row';
        var label = document.createElement('label');
        label.textContent = labelText;
        row.appendChild(label);
        row.appendChild(inputEl);
        return row;
    }

    function buildMultiplierOption(m, inputType, groupName) {
        var wrapper = document.createElement('div');
        wrapper.className = 'multiplier-option-block';

        var label = document.createElement('label');
        label.className = 'multiplier-option';

        var input = document.createElement('input');
        input.type = inputType;
        if (groupName) input.name = groupName;
        input.className = 'multiplier-input';
        input.dataset.multiplierId = m.id;
        input.dataset.type = m.factor_type;
        input.dataset.factor = m.factor_value !== null ? m.factor_value : '';
        input.dataset.label = m.label;

        label.appendChild(input);
        label.appendChild(document.createTextNode(' ' + m.label));
        wrapper.appendChild(label);

        if (m.factor_type === 'variable_multiply') {
            var varInput = document.createElement('input');
            varInput.type = 'number';
            varInput.step = '0.01';
            varInput.className = 'multiplier-variable-input';
            varInput.dataset.multiplierId = m.id;
            varInput.placeholder = 'valor';
            varInput.disabled = true;
            wrapper.appendChild(varInput);
        } else if (m.factor_type === 'add_per_unit') {
            var unitInput = document.createElement('input');
            unitInput.type = 'number';
            unitInput.step = '1';
            unitInput.className = 'multiplier-unit-input';
            unitInput.dataset.multiplierId = m.id;
            unitInput.placeholder = 'n';
            unitInput.disabled = true;
            wrapper.appendChild(unitInput);
        }

        return wrapper;
    }

    function buildMultipliers(product) {
        if (!product.multipliers.length) return null;

        var container = document.createElement('div');
        container.className = 'multipliers';
        var hint = document.createElement('p');
        hint.className = 'hint';
        hint.textContent = 'Multiplicadores aplicáveis';
        container.appendChild(hint);

        var i = 0;
        while (i < product.multipliers.length) {
            var m = product.multipliers[i];
            if (m.exclusive_group) {
                var group = document.createElement('div');
                group.className = 'multiplier-group';
                var groupName = 'group-' + product.id + '-' + m.exclusive_group;
                while (i < product.multipliers.length && product.multipliers[i].exclusive_group === m.exclusive_group) {
                    group.appendChild(buildMultiplierOption(product.multipliers[i], 'radio', groupName));
                    i++;
                }
                container.appendChild(group);
            } else {
                container.appendChild(buildMultiplierOption(m, 'checkbox', null));
                i++;
            }
        }
        return container;
    }

    function buildFieldsPanel(product) {
        var container = document.createElement('div');
        container.className = 'valuation-fields';

        if (product.valuation_criteria) {
            var critHint = document.createElement('p');
            critHint.className = 'hint';
            critHint.textContent = 'Critério: ' + product.valuation_criteria;
            container.appendChild(critHint);
        }
        if (product.base_value_note) {
            var noteHint = document.createElement('p');
            noteHint.className = 'hint warn';
            noteHint.textContent = product.base_value_note;
            container.appendChild(noteHint);
        }

        var qtyInput = document.createElement('input');
        qtyInput.type = 'number';
        qtyInput.className = 'field-quantity';
        qtyInput.step = '0.01';
        qtyInput.value = '1';
        container.appendChild(createFieldRow(product.quantity_label || 'Quantidade', qtyInput));

        var baseInput = document.createElement('input');
        baseInput.type = 'number';
        baseInput.className = 'field-base-value';
        baseInput.step = '0.01';
        if (product.base_value !== null) baseInput.value = product.base_value;
        container.appendChild(createFieldRow('Valor base (R$)', baseInput));

        var multipliersEl = buildMultipliers(product);
        if (multipliersEl) container.appendChild(multipliersEl);

        var notesInput = document.createElement('input');
        notesInput.type = 'text';
        notesInput.className = 'field-notes';
        notesInput.maxLength = 255;
        container.appendChild(createFieldRow('Observações (opcional)', notesInput));

        var previewDiv = document.createElement('div');
        previewDiv.className = 'computed-preview';
        previewDiv.appendChild(document.createTextNode('Sugestão calculada: '));
        var previewStrong = document.createElement('strong');
        previewStrong.className = 'preview-value';
        previewStrong.textContent = 'R$ 0,00';
        previewDiv.appendChild(previewStrong);
        var useBtn = document.createElement('button');
        useBtn.type = 'button';
        useBtn.className = 'use-suggestion-btn';
        useBtn.textContent = 'Usar este valor';
        previewDiv.appendChild(useBtn);
        container.appendChild(previewDiv);

        var finalInput = document.createElement('input');
        finalInput.type = 'number';
        finalInput.className = 'field-final-value';
        finalInput.step = '0.01';
        container.appendChild(createFieldRow('Valor final a salvar (R$)', finalInput));

        var confirmBtn = document.createElement('button');
        confirmBtn.type = 'button';
        confirmBtn.className = 'confirm-btn';
        confirmBtn.textContent = 'OK — Confirmar item';
        container.appendChild(confirmBtn);

        var statusSpan = document.createElement('span');
        statusSpan.className = 'save-status';
        container.appendChild(statusSpan);

        return container;
    }

    function computePanel(fieldsEl) {
        var quantity = parseFloat(fieldsEl.querySelector('.field-quantity').value) || 1;
        var baseValue = parseFloat(fieldsEl.querySelector('.field-base-value').value) || 0;
        var multiplierProduct = 1;
        var additive = 0;
        var applied = [];

        fieldsEl.querySelectorAll('.multiplier-input').forEach(function (input) {
            if (!input.checked) return;
            var type = input.dataset.type;
            var factor = input.dataset.factor !== '' ? parseFloat(input.dataset.factor) : null;
            var id = input.dataset.multiplierId;
            var label = input.dataset.label;

            if (type === 'multiply') {
                multiplierProduct *= factor;
                applied.push({ id: id, label: label, factor_type: type, factor_value: factor });
            } else if (type === 'variable_multiply') {
                var varInput = fieldsEl.querySelector('.multiplier-variable-input[data-multiplier-id="' + id + '"]');
                var varValue = parseFloat(varInput.value) || 1;
                multiplierProduct *= varValue;
                applied.push({ id: id, label: label, factor_type: type, variable_input: varValue });
            } else if (type === 'add_per_unit') {
                var unitInput = fieldsEl.querySelector('.multiplier-unit-input[data-multiplier-id="' + id + '"]');
                var n = parseFloat(unitInput.value) || 0;
                additive += n * factor;
                applied.push({ id: id, label: label, factor_type: type, unit_quantity: n, factor_value: factor });
            }
        });

        var totalMultiplier = multiplierProduct + additive;
        var value = baseValue * quantity * totalMultiplier;
        return { value: value, quantity: quantity, baseValue: baseValue, applied: applied };
    }

    function updateRowBadge(row, addedValue) {
        var currentTotal = parseFloat(row.dataset.valuationTotal || '0');
        var currentCount = parseInt(row.dataset.valuationCount || '0', 10);
        currentTotal += addedValue;
        currentCount += 1;
        row.dataset.valuationTotal = currentTotal;
        row.dataset.valuationCount = currentCount;

        var statusCell = row.querySelector('.valuation-status');
        statusCell.innerHTML = '';
        var badge = document.createElement('span');
        badge.className = 'valued-badge';
        badge.textContent = '✓ R$ ' + formatBRL(currentTotal) + (currentCount > 1 ? ' (' + currentCount + 'x)' : '');
        statusCell.appendChild(badge);
    }

    function updateYearTotal(total) {
        var el = document.getElementById('year-total');
        if (el) el.textContent = formatBRL(total);
    }

    function wireFieldsEvents(fieldsEl, row, product) {
        function updatePreview() {
            var result = computePanel(fieldsEl);
            fieldsEl.querySelector('.preview-value').textContent = 'R$ ' + formatBRL(result.value);
        }

        fieldsEl.querySelectorAll('.field-quantity, .field-base-value').forEach(function (input) {
            input.addEventListener('input', updatePreview);
        });

        fieldsEl.querySelectorAll('.multiplier-input').forEach(function (input) {
            input.addEventListener('change', function () {
                var id = input.dataset.multiplierId;
                var varInput = fieldsEl.querySelector('.multiplier-variable-input[data-multiplier-id="' + id + '"]');
                var unitInput = fieldsEl.querySelector('.multiplier-unit-input[data-multiplier-id="' + id + '"]');
                if (varInput) varInput.disabled = !input.checked;
                if (unitInput) unitInput.disabled = !input.checked;
                updatePreview();
            });
        });

        fieldsEl.querySelectorAll('.multiplier-variable-input, .multiplier-unit-input').forEach(function (input) {
            input.addEventListener('input', updatePreview);
        });

        fieldsEl.querySelector('.use-suggestion-btn').addEventListener('click', function () {
            var result = computePanel(fieldsEl);
            fieldsEl.querySelector('.field-final-value').value = result.value.toFixed(2);
        });

        fieldsEl.querySelector('.confirm-btn').addEventListener('click', function () {
            confirmFileEntry(fieldsEl, row, product);
        });

        updatePreview();
    }

    function confirmFileEntry(fieldsEl, row, product) {
        var statusEl = fieldsEl.querySelector('.save-status');
        var finalValueInput = fieldsEl.querySelector('.field-final-value');
        var finalValue = parseFloat(finalValueInput.value);

        if (Number.isNaN(finalValue)) {
            statusEl.textContent = 'Informe o valor final antes de confirmar.';
            statusEl.className = 'save-status error';
            return;
        }

        var result = computePanel(fieldsEl);
        var payload = {
            product_id: product.id,
            quantity: result.quantity,
            base_value: result.baseValue,
            final_value: finalValue,
            notes: fieldsEl.querySelector('.field-notes').value,
            applied_multipliers: result.applied,
            file_path: row.dataset.filePath,
            file_name: row.dataset.fileName
        };

        statusEl.textContent = 'Salvando...';
        statusEl.className = 'save-status';

        fetch(config.entryCreateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': config.csrfToken
            },
            body: JSON.stringify(payload)
        })
            .then(function (response) {
                if (!response.ok) throw new Error('Falha ao salvar.');
                return response.json();
            })
            .then(function (data) {
                statusEl.textContent = '✓ Item adicionado.';
                statusEl.className = 'save-status success';
                updateRowBadge(row, finalValue);
                updateYearTotal(data.total);

                fieldsEl.querySelector('.field-quantity').value = 1;
                fieldsEl.querySelector('.field-notes').value = '';
                finalValueInput.value = '';
                fieldsEl.querySelectorAll('.multiplier-input').forEach(function (input) { input.checked = false; });
                fieldsEl.querySelectorAll('.multiplier-variable-input, .multiplier-unit-input').forEach(function (input) {
                    input.value = '';
                    input.disabled = true;
                });
                var previewResult = computePanel(fieldsEl);
                fieldsEl.querySelector('.preview-value').textContent = 'R$ ' + formatBRL(previewResult.value);
            })
            .catch(function () {
                statusEl.textContent = 'Erro ao salvar. Tente novamente.';
                statusEl.className = 'save-status error';
            });
    }

    function buildPanelSkeleton(panel, row) {
        var selectRow = document.createElement('div');
        selectRow.className = 'field-row';
        var label = document.createElement('label');
        label.textContent = 'Item da tabela';
        var select = document.createElement('select');
        select.className = 'valuation-product-select';

        var blankOption = document.createElement('option');
        blankOption.value = '';
        blankOption.textContent = 'Selecionar item...';
        select.appendChild(blankOption);

        catalog.forEach(function (category) {
            var optgroup = document.createElement('optgroup');
            optgroup.label = category.name;
            category.products.forEach(function (product) {
                var option = document.createElement('option');
                option.value = product.id;
                option.textContent = product.name;
                optgroup.appendChild(option);
            });
            select.appendChild(optgroup);
        });

        selectRow.appendChild(label);
        selectRow.appendChild(select);
        panel.appendChild(selectRow);

        var fieldsContainer = document.createElement('div');
        panel.appendChild(fieldsContainer);

        select.addEventListener('change', function () {
            fieldsContainer.innerHTML = '';
            var productId = select.value;
            if (!productId) return;
            var product = findProduct(productId);
            if (!product) return;
            var fieldsEl = buildFieldsPanel(product);
            fieldsContainer.appendChild(fieldsEl);
            wireFieldsEvents(fieldsEl, row, product);
        });

        var closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'close-panel-btn';
        closeBtn.textContent = 'Fechar';
        closeBtn.addEventListener('click', function () {
            row.nextElementSibling.hidden = true;
        });
        panel.appendChild(closeBtn);
    }

    document.querySelectorAll('.valorar-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var row = btn.closest('tr');
            var detailRow = row.nextElementSibling;
            var panel = detailRow.querySelector('.file-valuation-panel');

            if (!panel.dataset.built) {
                buildPanelSkeleton(panel, row);
                panel.dataset.built = '1';
            }

            detailRow.hidden = !detailRow.hidden;
        });
    });
})();
