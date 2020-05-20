import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Select2Module } from 'ng2-select2';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { DimensionOptionsComponent } from './dimension-options.component';
import { AxisLabelerComponent } from './axis-labeler/axis-labeler.component';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Dimension } from 'src/app/shared/models/plot-builder';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Subject } from 'rxjs';

describe('DimensionOptionsComponent', () => {
  let component: DimensionOptionsComponent;
  let fixture: ComponentFixture<DimensionOptionsComponent>;
  let mockPlotService;

  beforeEach(async(() => {
    mockPlotService = jasmine.createSpyObj([
      'getDimDropdownValue',
      'getLabelBuilder',
      'updateFormatString',
      'getUpdatedLabelBuilder'
    ]);
    mockPlotService.getDimDropdownValue.and.returnValue('0');
    mockPlotService.getUpdatedLabelBuilder.and.returnValue(
      new Subject().asObservable()
    );
    TestBed.configureTestingModule({
      declarations: [ DimensionOptionsComponent, AxisLabelerComponent ],
      providers: [{
        provide: PlotService,
        useValue: mockPlotService
      }],
      imports: [
        Select2Module,
        FormsModule,
        HttpClientModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DimensionOptionsComponent);
    component = fixture.componentInstance;
    component.dimension = new Dimension();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
