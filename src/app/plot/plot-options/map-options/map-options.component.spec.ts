import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { MapOptionsComponent } from './map-options.component';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { AxisOption } from 'src/app/shared/models/plotly-builder';
import { PlotService } from 'src/app/shared/services/plot.service';


const testBrick66 = require('src/app/shared/test/brick_metadata_test_66.json');
const axisOptions = require('src/app/shared/test/axis-options.json');
const brick3 = require('src/app/shared/test/brick_metadata_test_3.json');

describe('MapOptionsComponent', () => {

  // const dimContext = brick3.results.dim_context;
  const mapBuilder = new MapBuilder(false);
  mapBuilder.dimWithCoords = 0;

  let spectator: Spectator<MapOptionsComponent>;
  let createComponent = createComponentFactory({
    component: MapOptionsComponent,
  })

  beforeEach(() => {
    spectator = createComponent({
      props: {
        mapBuilder,
        options: PlotService.mapBrickPropertiesToAxisOptions(testBrick66),
        dimensions: testBrick66.dim_context
      }
    });
  });

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should display correct items according to scalar type', () => {
    expect(spectator.component.colorOptions).toHaveLength(3);
    expect(spectator.component.labelOptions).toHaveLength(7);
  });

  it('should set dimension constraints when color is selected', () => {
    spyOn(spectator.component, 'setColorOptions').and.callThrough();
    spyOn(spectator.component.mapBuilder, 'setConstraints').and.callThrough();
    spectator.triggerEventHandler('ng-select#map-color', 'change', spectator.component.colorOptions[0]);
    spectator.detectChanges();
    
    expect(spectator.component.setColorOptions).toHaveBeenCalled();
    expect(spectator.component.mapBuilder.setConstraints).toHaveBeenCalled();
    expect(spectator.component.mapBuilder.constrainingRequired).toBeFalsy();

    // all dimension constraints should be disabled because a property from the same dimension as lat and long was selected
    const allConstraintsDisabled = spectator.component.mapBuilder.constraints.reduce((a, c) => c.disabled, false);
    expect(allConstraintsDisabled).toBeTruthy();
  });

  it('shouuld set dimensinon constraints when label is selected', () => {
    spyOn(spectator.component, 'setLabelOptions').and.callThrough();
    spyOn(spectator.component.mapBuilder, 'setConstraints').and.callThrough();
    // select last element from dropdown (data variable)
    spectator.triggerEventHandler('ng-select#map-labels', 'change', spectator.component.labelOptions[6]);
    spectator.detectChanges();

    expect(spectator.component.setLabelOptions).toHaveBeenCalled();
    expect(spectator.component.mapBuilder.setConstraints).toHaveBeenCalled();
    expect(spectator.component.mapBuilder.constraints[0].disabled).toBeTruthy();

    const dimsToBeConstrained = spectator.component.mapBuilder.constraints.slice(1);
    expect(dimsToBeConstrained.reduce((a, c) => c.disabled, false)).toBeTruthy();
  });

});

