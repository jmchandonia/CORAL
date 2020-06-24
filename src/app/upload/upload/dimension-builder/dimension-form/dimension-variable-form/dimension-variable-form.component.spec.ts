import { async, ComponentFixture, TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { DimensionVariableFormComponent } from './dimension-variable-form.component';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { ModalModule } from 'ngx-bootstrap/modal';
import { HttpClientModule } from '@angular/common/http';
import { DimensionVariable, BrickDimension, Brick, MicroType } from 'src/app/shared/models/brick';
const metadata = require('src/app/shared/test/brick-type-templates.json');
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { By } from '@angular/platform-browser';
import { of, Subject, asyncScheduler, Observable } from 'rxjs';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { NgSelectModule } from '@ng-select/ng-select';
import { FormsModule } from '@angular/forms';

describe('DimensionVariableFormComponent', () => {

  const errorSub = new Subject();

  const brick: Brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);

  const variables: DimensionVariable[] = brick.dimensions[0].variables;

  let variable: DimensionVariable = variables[0];


  const MockModalService = {
    show: (): BsModalRef => {
      return {
        hide: null, 
        content: {},
        setClass: null
      }
    },
    onHidden: of({}, asyncScheduler)
  };

  const MockUploadService = {
    searchDimensionVariableMicroTypes: (term: string): Observable<any> => of({
      results: [{id: '33333', text: 'test dim var type'}]
    }, asyncScheduler),
    getValidationErrors: errorSub,
    searchOntPropertyUnits: (microtype: MicroType): Observable<any> => of({
      results: [{id: '44444', text: 'test dim var unit'}]
    }, asyncScheduler)
  };

  let spectator: Spectator<DimensionVariableFormComponent>;
  const createComponent = createComponentFactory({
    component: DimensionVariableFormComponent,
    imports: [
      TooltipModule.forRoot(),
      HttpClientModule,
      ModalModule.forRoot(),
      NgSelectModule,
      FormsModule
    ],
    providers: [
      mockProvider(BsModalService, MockModalService),
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, {
        getValidationErrors: () => errorSub
      })
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {dimVar: variable}
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
    expect(spectator.component.dimVar).toEqual(variables[0]);
  });

  it('should not render units for unitless dimVar', () => {
    expect(spectator.component.dimVar.type.has_units).toBeFalsy();
    expect(spectator.query('div.no-units')).not.toBeNull();
    expect(spectator.queryAll('ng-select')).toHaveLength(1);
  });

  it('should disallow editing on required dim vars', () => {
    const selectEl = spectator.debugElement.query(By.css('ng-select'));
    expect(selectEl.nativeElement.getAttribute('ng-reflect-readonly')).toBe('true');
    expect(spectator.query('button.delete-dim-var')).toBeNull();
  });

  it('should open conext modal and emit new value', fakeAsync(() => {
    const modal = spectator.fixture.debugElement.injector.get(BsModalService);
    spyOn(spectator.component.reset, 'emit');
    spyOn(modal, 'show').and.callThrough();
    spyOn(modal.onHidden, 'subscribe').and.callThrough();
    spyOn(spectator.component, 'openModal').and.callThrough();
    spectator.click('button.select-custom-button');
    expect(spectator.component.openModal).toHaveBeenCalled();
    tick();
    spectator.detectChanges();
    expect(modal.onHidden.subscribe).toHaveBeenCalled();
    spectator.detectChanges();
    expect(spectator.component.reset.emit).toHaveBeenCalled();

    // reset dimVar to dim var that has units and context
    variable = variables[1];
  }));

  it('should render context', () => {
    expect(spectator.component.typeData[0].text).toBe('Volume, State=extracted from sediment');
  });

  it('should display units for dim var with units', () => {
    expect(spectator.query('.units-container > ng-select')).not.toBeNull();
    expect(spectator.query('no-units')).toBeNull();
    expect(spectator.component.unitsData[0].text).toBe('microliter');

    // reset dimVar to new instance of customizable dimVar
    variable = new DimensionVariable(brick.dimensions[0], false);
  });

  it('should call get units on selection', fakeAsync(() => {
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spectator.detectChanges();
    spyOn(uploadService, 'searchOntPropertyUnits').and.callThrough();
    spyOn(spectator.component, 'setDimVarType').and.callThrough();
    spectator.triggerEventHandler('ng-select', 'change', variables[1].typeTerm);
    spectator.detectChanges();
    expect(spectator.component.setDimVarType).toHaveBeenCalled();
    spectator.detectChanges();
    tick();
    expect(spectator.component.unitsData[0].text).toBe('test dim var unit')
  }));

  it('should display errors', () => {
    errorSub.next(true);
    expect(spectator.component.error).toBeTruthy();
    spectator.detectChanges();
    expect(spectator.query('.units-container > ng-select')).toHaveClass('select-error');
  });
});
