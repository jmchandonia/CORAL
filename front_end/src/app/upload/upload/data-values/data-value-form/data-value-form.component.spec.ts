import { async, ComponentFixture, TestBed, tick, fakeAsync, flushMicrotasks, flush } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { ModalModule, BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { HttpClientModule } from '@angular/common/http';
import { DataValueFormComponent } from './data-value-form.component';
import { DataValue, MicroType, Term } from 'src/app/shared/models/brick';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
const templates = require('src/app/shared/test/brick-type-templates.json');
import { of, Subject, asyncScheduler, Observable } from 'rxjs';
import { EventEmitter } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { By } from '@angular/platform-browser';
import { NgSelectModule } from '@ng-select/ng-select';
import { FormsModule } from '@angular/forms';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

describe('DataValueFormComponent', () => {

  const dataValues = BrickFactoryService.createUploadInstance(templates.results[0].children[1]).dataValues;
  let dataValue: DataValue = dataValues[0];

  const MockUploadService = {
    searchOntPropertyUnits: (microType: MicroType): Observable<any> => of({
      results: [{id: '55555', text: 'test unit'}]
    }, asyncScheduler)
  }

  const errorSub = new Subject();
  const MockValidator = {
    getValidationErrors: () => errorSub
  };

  let spectator: Spectator<DataValueFormComponent>;
  const createComponent = createComponentFactory({
    component: DataValueFormComponent,
    imports: [
      TooltipModule.forRoot(),
      ModalModule.forRoot(),
      HttpClientModule,
      NgSelectModule,
      FormsModule
    ],
    providers: [
      {
        provide: BsModalService,
        useValue: {
          show: (): BsModalRef => {
            return {
              hide: null, 
              content: {},
              setClass: null
            }
          },
          onHidden: of({}, asyncScheduler)
        }
      },
      // mockProvider(UploadService, MockUploadService)
      {
        provide: UploadService,
        useValue: MockUploadService
      },
      {
        provide: UploadValidationService,
        useValue: MockValidator
      }
    ]
  });

  beforeEach(() => spectator =  createComponent({
    props: {
      dataValue: dataValue
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have instance of data value', () => {
    const { dataValue } = spectator.component;
    expect(dataValue instanceof DataValue).toBeTruthy();
    expect(dataValue.type.id).toBe('ME:XXXXX15');
    expect(dataValue.type.text).toBe('Concentration');
  });

  it('should open context', () => {
    spyOn(spectator.component, 'openContextModal');
    spectator.click('button.btn.select-custom-button');
    expect(spectator.component.openContextModal).toHaveBeenCalled();
  });

  it('should emit new value', fakeAsync(() => {
    const modalService = spectator.fixture.debugElement.injector.get(BsModalService);
    spyOn(spectator.component.reset, 'emit');
    spyOn(modalService.onHidden, 'subscribe').and.callThrough();
    spectator.component.openContextModal();
    tick();
    spectator.detectChanges();
    expect(modalService.onHidden.subscribe).toHaveBeenCalled();
    spectator.detectChanges();
    expect(spectator.component.reset.emit).toHaveBeenCalled(); 

  }));

  it('should render dropdown for item with units', () => {
    // first item we are testing is an item that has units
    expect(spectator.component.dataValue.type.has_units).toBeTruthy();
    expect(spectator.component.unitsValues).toEqual([{id: 'UO:XXXXXX8', text: 'milligram per liter'}]);
    expect(spectator.component.dataValue.microType).toBeTruthy();
    expect(spectator.query('div.col-5.units-container > ng-select')).not.toBeNull();
    expect(spectator.query('div.row.justify-content-center.no-units')).toBeNull();
  });

  it('should call getUnits method and return units', fakeAsync(() => {
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'searchOntPropertyUnits').and.callThrough();
    spectator.component.getUnits();
    tick();
    spectator.detectChanges();
    expect(uploadService.searchOntPropertyUnits).toHaveBeenCalled();
    expect(uploadService.searchOntPropertyUnits).toHaveBeenCalledWith(spectator.component.dataValue.microType);
    expect(spectator.component.unitsValues).toHaveLength(1);
  }));

  it('should update units', () => {
    spyOn(spectator.component, 'validate');
    spectator.component.updateUnits({id: 'XXXXX', text: 'test units', has_units: false});
    expect(spectator.component.validate).toHaveBeenCalled();
    expect(spectator.component.dataValue.units.text).toBe('test units');
    expect(spectator.component.dataValue.units.id).toBe('XXXXX');
  });

  it('should disallow type selection for required data var', () => {
    expect(spectator.component.dataValue.required).toBeTruthy();
    const selectEl = spectator.debugElement.query(By.css('div.col-5.type-options-container > ng-select'));
    expect(selectEl.nativeElement.getAttribute('ng-reflect-readonly')).toBe('true');

    // switch dataValue to be the next item, Below, Relative=detection limit
    dataValue = dataValues[1];
  });

  it('should not display unit selector for unitless dataVars', () => {
    expect(spectator.component.dataValue.type.text).toBe('Below');
    expect(spectator.component.dataValue.microType.has_units).toBeFalsy();
    expect(spectator.query('div.no-units')).toBeTruthy();
    expect(spectator.query('div.units-container > ng-select')).toBeNull();
  });

  it('should render microtype context in dropdown', () => {
    spyOn(spectator.component, 'setContextLabel').and.callThrough();
    spyOn(spectator.component, 'updateType').and.callThrough();
      spectator.detectChanges();
      expect(spectator.component.dataValue.context).toHaveLength(1);
      expect(spectator.component.typeValues[0].text).toBe('Below, Relative=detection limit');

      // switch data value to instance of custom data value
    dataValue = new DataValue(2, false);
  });

  it('should have empty selectable type field for custom dataVar', () => {
    expect(spectator.component.dataValue.required).toBeFalsy();
    const selectEl = spectator.debugElement.query(By.css('div.col-5.type-options-container > ng-select'));
    expect(selectEl.nativeElement.getAttribute('ng-reflect-readonly')).toBe('false');
  });

  it('should start empty data var with no unit selector', () => {
    expect(spectator.query('div.no-units')).toBeTruthy();
    expect(spectator.query('div.units-container > ng-select')).toBeNull();
  });

  it('should select and update type', () => {
    spyOn(spectator.component, 'getUnits').and.callThrough();
    spectator.component.updateType(dataValues[0].typeTerm);
    spectator.detectChanges();
    expect(spectator.component.dataValue.type.text).toBe('Concentration');
    expect(spectator.component.dataValue.units).toBeUndefined();  
    expect(spectator.component.getUnits).toHaveBeenCalled(); 
  });

  it('should subscribe to errors', () => {
    errorSub.next(true);
    spectator.detectChanges();

    expect(spectator.component.error).toBeTruthy();
    expect(spectator.query('ng-select.units-selector')).toHaveClass('select-error');
  });


});
