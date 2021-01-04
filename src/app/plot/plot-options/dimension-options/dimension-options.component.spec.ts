import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { DimensionOptionsComponent } from './dimension-options.component';
import { AxisLabelerComponent } from './axis-labeler/axis-labeler.component';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Dimension } from 'src/app/shared/models/plot-builder';
import { Subject } from 'rxjs';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { NgSelectModule } from '@ng-select/ng-select';
const metadata = require('src/app/shared/test/object-metadata.json');

xdescribe('DimensionOptionsComponent', () => {

  const testDimension = new Dimension(metadata.dim_context, metadata.typed_values);

  const MockPlotService = {
    // getDimDropdownValue: () => '0',
    // setPlotlyDataAxis: (axis, value) => {}
  };

  let spectator: Spectator<DimensionOptionsComponent>;
  const createComponent = createComponentFactory({
    component: DimensionOptionsComponent,
    imports: [
      HttpClientModule,
      NgSelectModule,
      FormsModule
    ],
    entryComponents: [
      MockComponent(AxisLabelerComponent)
    ],
    providers: [
      mockProvider(PlotService, MockPlotService)
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      dimension: testDimension,
      dimensionLabel: 'X axis',
      index: 0
    }
  }));

  afterEach(() => delete testDimension.dimVars);

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
    expect(spectator.component.dimension).toEqual(testDimension);
  });

  it('should set axis label and title', () => {
    expect(spectator.component.axis).toBe('x');
    expect(spectator.component.dimensionLabel).toBe('X axis')
  });

  it('should set value from list of dimensions', () => {
    // const mockPlotService = spectator.fixture.debugElement.injector.get(PlotService);
    // spyOn(mockPlotService, 'setPlotlyDataAxis');
    // spectator.component.setSelectedDimension({id: '1'});
    // expect(mockPlotService.setPlotlyDataAxis).toHaveBeenCalledWith('x', '1');
    // expect(spectator.component.dimension.dimVars).toEqual(metadata.dim_context[1].typed_values);
    // expect(spectator.component.dimension.dimVars[0].selected).toBeTruthy();
    // expect(spectator.component.showDisplayValues).toBeTruthy();\
  });

  it('should set label pattern correctly when dimension is selected', () => {
    spyOn(spectator.component, 'setLabelPattern');
    spectator.component.setSelectedDimension({id: '1'});
    spectator.detectChanges();
    expect(spectator.component.setLabelPattern).toHaveBeenCalled();
    expect(spectator.query('.axis-labeler-container')).not.toBeHidden();
    expect(testDimension.label_pattern).toBe('Sequence Type=#V1, Strand=#V2');
  });
});
