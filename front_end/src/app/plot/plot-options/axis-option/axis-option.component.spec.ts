import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { AxisOptionComponent } from './axis-option.component';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { PlotlyBuilder, Axis } from 'src/app/shared/models/plotly-builder';

const axisOptions = require('src/app/shared/test/axis-options.json'); // pulled from well axis options
const plotTypes = require('src/app/shared/test/plot-types.json');

let spectator: Spectator<AxisOptionComponent>;
let invalid = false;

const createComponent = createComponentFactory({
  component: AxisOptionComponent,
})

describe('AxisOptionComponent', () => {

  const mockPlotlyBuilder = new PlotlyBuilder(true);

  beforeEach(() => {
    spectator = createComponent({
      props: {
        axisValidation: plotTypes.results[0].axis_data.y,
        options: axisOptions.results,
        axis: mockPlotlyBuilder.axes.y,
        invalid
      }
    });
  });

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should filter out non numeric options for numeric axes', () => {
    expect(spectator.component.options).toHaveLength(9)
    expect(spectator.component.validOptions).toHaveLength(2);
  });

  it('should call emit changes to parent component', () => {
    spyOn(spectator.component, 'setAxis').and.callThrough();
    spyOn(spectator.component.selected, 'emit');

    spectator.triggerEventHandler('ng-select', 'change', spectator.component.validOptions[0]);
    spectator.detectChanges();

    expect(spectator.component.setAxis).toHaveBeenCalledWith(spectator.component.validOptions[0]);
    expect(spectator.component.selected.emit).toHaveBeenCalledWith(spectator.component.axis.data);
  });

  it('should clear selection properly', () => {
    spyOn(spectator.component, 'handleClear').and.callThrough();
    spyOn(spectator.component, 'setAxis').and.callThrough();
    spyOn(spectator.component.selected, 'emit');
    spyOn(spectator.component.selectionCleared, 'emit');

    spectator.triggerEventHandler('ng-select', 'clear', null);
    spectator.detectChanges();

    expect(spectator.component.selected.emit).not.toHaveBeenCalled();
    expect(spectator.component.handleClear).toHaveBeenCalled();
    expect(spectator.component.selectionCleared.emit).toHaveBeenCalled();

    const axis = spectator.component.axis;
    expect(axis.data).toBeUndefined();
    expect(axis.dim_idx).toBeUndefined();
    expect(axis.data_var_idx).toBeUndefined();
    expect(axis.dim_var_idx).toBeUndefined();
    expect(axis.title).toBe('');
  });

  it('should display invalid text', () => {
    spectator.component.invalid = true;
    spectator.detectChanges();

    expect(spectator.query('ng-select')).toHaveClass('select-error');
  })
});
