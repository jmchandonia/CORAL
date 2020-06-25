import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ContextFormComponent } from './context-form.component';
import { NgSelectModule } from '@ng-select/ng-select';
import { Context } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { of, Subject } from 'rxjs';
import { Term, MicroType } from '../../../../../../shared/models/brick';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

describe('ContextFormComponent', () => {
  let spectator: Spectator<ContextFormComponent>;

  const MockUploadService = {
    searchPropertyMicroTypes: (term: string) => {
      return of({
        results: {id: 'test', text: 'test item', has_units: true}
      });
    },
    searchOntPropertyValues: (term: string, microtype: MicroType) => {
      return of({
        results: [{id: 'test1', text: 'test oterm', has_units: false}]
      });
    },
    searchOntPropertyUnits: (microtype: MicroType) => {
      return of({
        results: [{id: 'test2', text: 'test units', has_units: false}]
      });
    }
  }

  const errorSub = new Subject();
  const MockValidator = {
    getContextValidationErrors: () => errorSub
  };

  const createComponent = createComponentFactory({
    component: ContextFormComponent,
    imports: [
      FormsModule,
      HttpClientModule,
      NgSelectModule
    ],
    providers: [
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, MockValidator)
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      context: new Context()
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
    expect(spectator.component.context).toBeTruthy();
  });

  it('should hanldle type search', fakeAsync(() => {
    const uploadService = spectator.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'searchPropertyMicroTypes').and.callThrough();
    spyOn(spectator.component, 'handleTypesSearch').and.callThrough();

    spectator.typeInElement('t', 'ng-select input');
    spectator.detectChanges();

    expect(spectator.component.handleTypesSearch).toHaveBeenCalled();
    expect(uploadService.searchPropertyMicroTypes).toHaveBeenCalledWith('t'); 
    tick();
    spectator.detectChanges();
    expect(spectator.component.typesData).toEqual([{id: 'test', text: 'test item', has_units: true}]);
  }));

  it('should set context type', () => {
    spyOn(spectator.component, 'setContextType').and.callThrough();
    spyOn(spectator.component, 'getUnits');

    spectator.triggerEventHandler('ng-select.type-selector', 'change', {
      id: 'test',
      text: 'test item',
      has_units: true
    });

    spectator.detectChanges();
    expect(spectator.component.setContextType).toHaveBeenCalledWith({
      id: 'test',
      text: 'test item',
      has_units: true
    });
    expect(spectator.component.getUnits).toHaveBeenCalled();
  });

  it('should handle values search', fakeAsync(() => {
    const uploadService = spectator.debugElement.injector.get(UploadService);
    spyOn(spectator.component, 'handleValuesSearch').and.callThrough();
    spyOn(uploadService, 'searchOntPropertyValues').and.callThrough();
    spectator.component.context.scalarType = 'oterm_ref';
    spectator.component.context.type = new Term('test', 'test');
    spectator.detectChanges();

    expect(spectator.query('ng-select.value-selector')).not.toBeNull();
    spectator.typeInElement('t', 'ng-select.value-selector input');
    spectator.detectChanges();

    expect(spectator.component.handleValuesSearch).toHaveBeenCalled();
    expect(uploadService.searchOntPropertyValues).toHaveBeenCalled();
    tick();
    expect(spectator.component.valuesData).toEqual([{id: 'test1', text: 'test oterm', has_units: false}]);
  }));

  it('should set context value', () => {
    spyOn(spectator.component, 'setValue').and.callThrough();
    spectator.component.context.scalarType = 'oterm_ref';
    spectator.component.context.type = new Term('test', 'test');
    spectator.detectChanges();
    spectator.triggerEventHandler('ng-select.value-selector', 'change', {
      id: 'test1',
      text: 'test oterm',
      has_units: false
    });
    spectator.detectChanges();

    expect(spectator.component.setValue).toHaveBeenCalled();
    expect(spectator.component.context.value).toEqual({
      id: 'test1',
      text: 'test oterm',
      has_units: false
    });
  });

  it('should get units', fakeAsync(() => {
    const uploadService = spectator.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'searchOntPropertyUnits').and.callThrough();

    spectator.component.context.type = new Term('test', 'test');
    spectator.detectChanges();
    spectator.component.getUnits();

    expect(uploadService.searchOntPropertyUnits).toHaveBeenCalledWith(spectator.component.context.microType);
    tick();
    spectator.detectChanges();
    expect(spectator.component.unitsData).toEqual([{
      id: 'test2',
      text: 'test units',
      has_units: false
    }]);
    expect(spectator.query('ng-select.units-selector')).not.toBeNull();
  }));

  it('should set units', () => {
    spyOn(spectator.component, 'setUnits').and.callThrough();
    spectator.component.context.type = new Term('test', 'test');
    spectator.detectChanges();

    spectator.triggerEventHandler('ng-select.units-selector', 'change', {
      id: 'test2',
      text: 'test units',
      has_units: false
    });
    spectator.detectChanges();

    expect(spectator.component.setUnits).toHaveBeenCalled();
    expect(spectator.component.context.units).toEqual({
      id: 'test2',
      text: 'test units',
      has_units: false
    });
  });

  it('should validate errors', () => {
    errorSub.next(true);
    spectator.detectChanges();
    expect(spectator.query('ng-select.type-selector')).toHaveClass('select-error');
  });
});
